import hashlib
import imagehash
from PIL import Image
import io


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def phash_bytes(data: bytes) -> str:
    """Perceptual hash for similarity comparison — images only."""
    image = Image.open(io.BytesIO(data)).convert("RGB")
    return str(imagehash.phash(image))


def phash_distance(hash_a: str, hash_b: str) -> int:
    """Hamming distance between two pHash strings (lower = more similar)."""
    a = imagehash.hex_to_hash(hash_a)
    b = imagehash.hex_to_hash(hash_b)
    return a - b


def similarity_score(phash_a: str, phash_b: str) -> int:
    """Returns 0–100 similarity score (100 = identical)."""
    distance = phash_distance(phash_a, phash_b)
    # pHash produces 64-bit hash; max distance = 64
    return max(0, round((1 - distance / 64) * 100))
