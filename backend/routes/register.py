from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from models.schemas import RegisterRequest, RegisterResponse
from services.solana import register_media
from utils.db import get_db, MediaRecord

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
        registered_at=now,
    )
    db.add(record)
    await db.commit()

    return RegisterResponse(
        tx_signature=tx_sig,
        hash=body.hash,
        cid=body.cid,
        wallet_address=body.wallet_address,
        timestamp=now,
        on_chain=not tx_sig.startswith("MOCK_"),
    )
