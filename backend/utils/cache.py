"""
Redis cache for verification results.

Keys:   verify:{sha256_hash}
TTL:    1 hour — long enough to avoid redundant AI calls, short enough
        that new registrations eventually affect results.
"""
import json
from typing import Optional

try:
    import redis.asyncio as aioredis
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

from config import settings

_client: Optional[object] = None
_TTL = 3600


def _get_client():
    global _client
    if not _REDIS_AVAILABLE:
        return None
    if _client is None:
        _client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def get_cached_verification(sha256: str) -> Optional[dict]:
    client = _get_client()
    if client is None:
        return None
    try:
        raw = await client.get(f"verify:{sha256}")
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def set_cached_verification(sha256: str, result: dict) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        await client.setex(f"verify:{sha256}", _TTL, json.dumps(result, default=str))
    except Exception:
        pass


async def invalidate_verification(sha256: str) -> None:
    """Call this when a hash gets registered so cached 'Unknown' results are cleared."""
    client = _get_client()
    if client is None:
        return
    try:
        await client.delete(f"verify:{sha256}")
    except Exception:
        pass
