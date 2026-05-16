from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from utils.db import get_db, MediaRecord

router = APIRouter()


class MediaLookupResponse(BaseModel):
    hash: str
    cid: str
    phash: Optional[str]
    wallet_address: str
    tx_signature: str
    on_chain: bool
    registered_at: datetime


@router.get("/media/{hash}", response_model=MediaLookupResponse)
async def get_media(hash: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MediaRecord).where(MediaRecord.sha256_hash == hash)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Media not registered")

    return MediaLookupResponse(
        hash=record.sha256_hash,
        cid=record.ipfs_cid,
        phash=record.phash,
        wallet_address=record.wallet_address,
        tx_signature=record.tx_signature,
        on_chain=not record.tx_signature.startswith("MOCK_"),
        registered_at=record.registered_at,
    )
