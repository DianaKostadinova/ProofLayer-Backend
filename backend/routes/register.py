from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import traceback

from models.schemas import RegisterRequest, RegisterResponse
from services.solana import register_media
from utils.db import get_db, MediaRecord
from utils.cache import invalidate_verification

router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
async def register_provenance(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    # Prevent duplicate registrations
    existing = await db.execute(
        select(MediaRecord).where(MediaRecord.sha256_hash == body.hash)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Media already registered on-chain")

    try:
        # Verify the on-chain tx and get back the confirmed signature
        tx_sig = await register_media(
            sha256_hash=body.hash,
            ipfs_cid=body.cid,
            wallet_address=body.wallet_address,
            tx_signature=body.signature,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Solana registration failed: {exc}")

    now = datetime.now(timezone.utc)
    record = MediaRecord(
        sha256_hash=body.hash,
        ipfs_cid=body.cid,
        wallet_address=body.wallet_address,
        tx_signature=tx_sig,
        phash=body.phash,
        registered_at=now,
    )
    try:
        db.add(record)
        await db.commit()
    except Exception as db_exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"DB error: {db_exc}")
    await invalidate_verification(body.hash)

    return RegisterResponse(
        tx_signature=tx_sig,
        hash=body.hash,
        cid=body.cid,
        wallet_address=body.wallet_address,
        timestamp=now,
        on_chain=not tx_sig.startswith("MOCK_"),
    )
