from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# --- Upload ---

class UploadResponse(BaseModel):
    hash: str
    cid: str
    filename: str
    size_bytes: int


# --- Register ---

class RegisterRequest(BaseModel):
    hash: str
    cid: str
    wallet_address: str
    signature: str  # signed message from wallet proving ownership


class RegisterResponse(BaseModel):
    tx_signature: str
    hash: str
    cid: str
    wallet_address: str
    timestamp: datetime
    on_chain: bool


# --- Verify ---

class VerifyResponse(BaseModel):
    hash: str
    similarity: int                  # 0–100 perceptual similarity to known originals
    deepfake_probability: float      # 0.0–1.0
    status: str                      # "Authentic" | "Likely Manipulated" | "Unknown"
    registered_owner: Optional[str]  # wallet address of original registrant
    registered_at: Optional[datetime]
    ipfs_cid: Optional[str]


# --- DB Models (SQLAlchemy-compatible dict shapes) ---

class MediaRecordDB(BaseModel):
    id: Optional[int] = None
    sha256_hash: str
    ipfs_cid: str
    wallet_address: str
    tx_signature: str
    filename: Optional[str] = None
    registered_at: datetime

    class Config:
        from_attributes = True
