from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from sqlalchemy import func
from utils.db import get_db, MediaRecord, VerificationLog

router = APIRouter()


class MediaListItem(BaseModel):
    hash: str
    cid: str
    wallet_address: str
    tx_signature: str
    on_chain: bool
    registered_at: datetime
    filename: Optional[str] = None

    class Config:
        from_attributes = True


class VerifyHistoryItem(BaseModel):
    hash: str
    similarity: int
    deepfake_probability: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/media", response_model=list[MediaListItem])
async def list_media(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MediaRecord).order_by(desc(MediaRecord.registered_at)).limit(limit)
    )
    records = result.scalars().all()
    return [
        MediaListItem(
            hash=r.sha256_hash,
            cid=r.ipfs_cid,
            wallet_address=r.wallet_address,
            tx_signature=r.tx_signature,
            on_chain=not r.tx_signature.startswith("MOCK_"),
            registered_at=r.registered_at,
            filename=r.filename,
        )
        for r in records
    ]


@router.get("/verify/history", response_model=list[VerifyHistoryItem])
async def verify_history(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VerificationLog).order_by(desc(VerificationLog.created_at)).limit(limit)
    )
    logs = result.scalars().all()
    return [
        VerifyHistoryItem(
            hash=log.queried_hash,
            similarity=log.similarity,
            deepfake_probability=log.deepfake_probability,
            status=log.status,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    media_count = await db.scalar(select(func.count(MediaRecord.id)))
    verify_count = await db.scalar(select(func.count(VerificationLog.id)))
    manipulated = await db.scalar(
        select(func.count(VerificationLog.id)).where(VerificationLog.status != "Authentic")
    )
    return {
        "media_registered": media_count or 0,
        "verifications_run": verify_count or 0,
        "manipulations_detected": manipulated or 0,
    }
