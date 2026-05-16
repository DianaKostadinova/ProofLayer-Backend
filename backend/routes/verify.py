from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from models.schemas import VerifyResponse
from services.hashing import sha256_bytes
from services.verification import verify_media
from utils.db import get_db, VerificationLog
from utils.cache import get_cached_verification, set_cached_verification

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "video/mp4", "video/quicktime"}


@router.post("/verify", response_model=VerifyResponse)
async def verify(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported media type: {file.content_type}")

    data = await file.read()

    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    # Check cache first — skip AI pipeline for already-seen files
    sha256 = sha256_bytes(data)
    cached = await get_cached_verification(sha256)
    if cached:
        return VerifyResponse(**cached)

    try:
        result = await verify_media(data, file.filename or "upload", db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Verification failed: {exc}")

    # Cache and log
    await set_cached_verification(sha256, result)

    log = VerificationLog(
        queried_hash=result["hash"],
        similarity=result["similarity"],
        deepfake_probability=result["deepfake_probability"],
        status=result["status"],
    )
    db.add(log)
    await db.commit()

    return VerifyResponse(**result)
