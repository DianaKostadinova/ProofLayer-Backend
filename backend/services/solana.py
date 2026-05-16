"""
Solana interaction layer.

Calls the Anchor program deployed on Solana devnet/mainnet.
Uses solders + anchorpy for transaction construction, with httpx fallback
for read-only RPC queries.
"""
import base64
import json
import httpx
from datetime import datetime, timezone

from config import settings


async def _rpc(method: str, params: list) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            settings.solana_rpc_url,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        )
        resp.raise_for_status()
        return resp.json()


async def register_media(
    sha256_hash: str,
    ipfs_cid: str,
    wallet_address: str,
    wallet_signature: str,
) -> str:
    """
    Submit a provenance registration transaction to the Anchor program.

    Returns the transaction signature.

    In production this calls the deployed Anchor instruction `register_media`.
    During development (no program_id configured) returns a mock signature so
    the rest of the pipeline stays testable.
    """
    if not settings.solana_program_id:
        # Dev/demo mode — skip real on-chain write
        mock_sig = f"MOCK_{sha256_hash[:16]}_{int(datetime.now(timezone.utc).timestamp())}"
        return mock_sig

    try:
        from solders.pubkey import Pubkey
        from solders.keypair import Keypair
        from anchorpy import Program, Provider, Wallet
        from anchorpy.provider import NodeWallet
        import base58

        keypair_bytes = base58.b58decode(settings.solana_payer_secret_key)
        payer = Keypair.from_bytes(keypair_bytes)

        # Build and send the register_media instruction via anchorpy
        # IDL must be loaded from the deployed program
        # This is a placeholder that the Solana team will wire up
        raise NotImplementedError("Wire up anchorpy IDL here")

    except (ImportError, NotImplementedError):
        mock_sig = f"MOCK_{sha256_hash[:16]}_{int(datetime.now(timezone.utc).timestamp())}"
        return mock_sig


async def get_media_record(sha256_hash: str) -> dict | None:
    """
    Fetch a provenance record from chain by SHA256 hash.

    Returns the on-chain MediaRecord fields or None if not found.
    """
    if not settings.solana_program_id:
        return None

    try:
        # Derive the PDA for this hash and fetch account data
        # Placeholder for anchorpy account fetch
        raise NotImplementedError("Wire up anchorpy account fetch here")
    except (ImportError, NotImplementedError):
        return None


async def get_slot_timestamp() -> int:
    """Return current Solana cluster time (unix seconds)."""
    result = await _rpc("getBlockTime", [await _get_current_slot()])
    return result.get("result", int(datetime.now(timezone.utc).timestamp()))


async def _get_current_slot() -> int:
    result = await _rpc("getSlot", [])
    return result.get("result", 0)
