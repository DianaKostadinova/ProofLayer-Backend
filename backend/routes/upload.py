from fastapi import APIRouter, UploadFile, File, HTTPException
from models.schemas import UploadResponse
from services.hashing import sha256_bytes, phash_bytes
from services.ipfs import upload_file

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "video/mp4", "video/quicktime"}


@router.post("/upload", response_model=UploadResponse)
async def upload_media(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported media type: {file.content_type}")

    data = await file.read()

    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    sha256 = sha256_bytes(data)
    phash = phash_bytes(data)

    try:
        cid = await upload_file(data, file.filename or "upload")
    except Exception:
        # Pinata not configured or unreachable — store a local content-address
        # so the rest of the registration flow still works without IPFS.
        cid = f"LOCAL:{sha256}"

    return UploadResponse(
        hash=sha256,
        cid=cid,
        phash=phash,
        filename=file.filename or "upload",
        size_bytes=len(data),
    )
