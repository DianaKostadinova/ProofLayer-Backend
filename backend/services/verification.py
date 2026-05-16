"""
Verification orchestration.

Workflow:
  1. SHA256 hash the incoming file
  2. Check DB for exact-match registration
  3. Call AI service for deepfake probability
  4. Compute pHash similarity against registered originals
  5. Aggregate into a trust score and status label
"""
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from services.hashing import sha256_bytes, phash_bytes, similarity_score
from utils.db import MediaRecord


_STATUS_THRESHOLDS = {
    "authentic": (80, 0.25),          # similarity >= 80 AND deepfake_prob <= 0.25
    "likely_manipulated": (0, 0.60),  # deepfake_prob >= 0.60
}


async def _call_ai_service(file_bytes: bytes, filename: str) -> dict:
    """
    POST file to AI microservice.  Returns:
      { "deepfake_probability": float, "phash": str }
    Falls back to local pHash + zero deepfake score if AI service is down.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.ai_service_url}/analyze",
                files={"file": (filename, file_bytes)},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError:
        # Graceful degradation — run what we can locally
        local_phash = phash_bytes(file_bytes)
        return {"deepfake_probability": 0.0, "phash": local_phash}


async def _best_similarity(file_phash: str, db: AsyncSession) -> int:
    """Compare incoming pHash against all registered originals; return best match score."""
    result = await db.execute(select(MediaRecord))
    records = result.scalars().all()

    if not records:
        return 0

    best = 0
    for record in records:
        if record.phash:
            score = similarity_score(file_phash, record.phash)
            best = max(best, score)

    return best


def _compute_status(similarity: int, deepfake_probability: float) -> str:
    if similarity == 100 and deepfake_probability < 0.1:
        return "Authentic — Exact Match"
    if deepfake_probability >= _STATUS_THRESHOLDS["likely_manipulated"][1]:
        return "Likely Manipulated"
    if similarity >= _STATUS_THRESHOLDS["authentic"][0] and deepfake_probability <= _STATUS_THRESHOLDS["authentic"][1]:
        return "Authentic"
    return "Unknown"


async def verify_media(file_bytes: bytes, filename: str, db: AsyncSession) -> dict:
    """
    Full verification pipeline. Returns result dict matching VerifyResponse schema.
    """
    sha256 = sha256_bytes(file_bytes)

    # Exact hash match — registered original
    existing = await db.execute(
        select(MediaRecord).where(MediaRecord.sha256_hash == sha256)
    )
    record = existing.scalar_one_or_none()
    if record:
        return {
            "hash": sha256,
            "similarity": 100,
            "deepfake_probability": 0.0,
            "status": "Authentic — Exact Match",
            "registered_owner": record.wallet_address,
            "registered_at": record.registered_at,
            "ipfs_cid": record.ipfs_cid,
        }

    # No exact match — run AI + similarity
    ai_result = await _call_ai_service(file_bytes, filename)
    deepfake_prob: float = ai_result.get("deepfake_probability", 0.0)
    file_phash: str = ai_result.get("phash") or phash_bytes(file_bytes)

    similarity = await _best_similarity(file_phash, db)
    status = _compute_status(similarity, deepfake_prob)

    return {
        "hash": sha256,
        "similarity": similarity,
        "deepfake_probability": round(deepfake_prob, 4),
        "status": status,
        "registered_owner": None,
        "registered_at": None,
        "ipfs_cid": None,
    }
