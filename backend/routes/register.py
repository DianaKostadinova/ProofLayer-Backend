from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from models.schemas import RegisterRequest, RegisterResponse
from services.solana import register_media
from services.auth import verify_wallet_signature
from utils.db import get_db, MediaRecord
from utils.cache import invalidate_verification

router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
async def register_provenance(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    if not verify_wallet_signature(body.wallet_address, body.hash, body.signature):
        raise HTTPException(status_code=401, detail="Invalid wallet signature")

    # Prevent duplicate registrations
    existing = await db.execute(
        select(MediaRecord).where(MediaRecord.sha256_hash == body.hash)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Media already registered on-chain")

    try:
        tx_sig = await register_media(
            sha256_hash=body.hash,
            ipfs_cid=body.cid,
            wallet_address=body.wallet_address,
            wallet_signature=body.signature,
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
    db.add(record)
    await db.commit()
    await invalidate_verification(body.hash)

    return RegisterResponse(
        tx_signature=tx_sig,
        hash=body.hash,
        cid=body.cid,
        wallet_address=body.wallet_address,
        timestamp=now,
        on_chain=not tx_sig.startswith("MOCK_"),
    )
