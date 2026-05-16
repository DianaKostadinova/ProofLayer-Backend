import httpx
from config import settings


PINATA_UPLOAD_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"
PINATA_JSON_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"


def _auth_headers() -> dict:
    if settings.pinata_jwt:
        return {"Authorization": f"Bearer {settings.pinata_jwt}"}
    return {
        "pinata_api_key": settings.pinata_api_key,
        "pinata_secret_api_key": settings.pinata_secret_key,
    }


async def upload_file(file_bytes: bytes, filename: str) -> str:
    """Upload raw file bytes to IPFS via Pinata. Returns CID."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            PINATA_UPLOAD_URL,
            headers=_auth_headers(),
            files={"file": (filename, file_bytes)},
        )
        response.raise_for_status()
        return response.json()["IpfsHash"]


async def upload_metadata(metadata: dict) -> str:
    """Pin a JSON metadata object to IPFS. Returns CID."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            PINATA_JSON_URL,
            headers={**_auth_headers(), "Content-Type": "application/json"},
            json={"pinataContent": metadata},
        )
        response.raise_for_status()
        return response.json()["IpfsHash"]
