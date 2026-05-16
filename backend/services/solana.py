"""
Solana interaction layer.

The Anchor program (proof_layer) requires the user's wallet to sign transactions
(owner: Signer), so registration transactions are built and submitted by the
frontend via Phantom. This service:
  - Verifies a confirmed transaction involved our program (register_media)
  - Reads on-chain MediaRecord PDAs by deriving seeds ["media", sha256_hash]
  - Decodes raw Anchor account bytes without needing anchorpy
"""
import base64
import struct
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


def _derive_media_pda(sha256_hash_hex: str, program_id_str: str) -> tuple[str, int]:
    """Derive the MediaRecord PDA from the SHA256 hash. Seeds: [b'media', hash_bytes]"""
    from solders.pubkey import Pubkey
    hash_bytes = bytes.fromhex(sha256_hash_hex)
    program_id = Pubkey.from_string(program_id_str)
    pda, bump = Pubkey.find_program_address([b"media", hash_bytes], program_id)
    return str(pda), bump


def _decode_media_record(data: bytes) -> dict | None:
    """
    Decode raw Anchor MediaRecord account bytes.
    Layout: [8: discriminator][32: owner][32: sha256_hash][4+N: ipfs_cid][8: timestamp i64]
            [8: verification_count u64][1: bump u8]
    """
    import base58 as b58

    if len(data) < 8 + 32 + 32 + 4:
        return None

    offset = 8  # skip Anchor account discriminator

    owner = b58.b58encode(data[offset:offset + 32]).decode()
    offset += 32

    sha256_hash = data[offset:offset + 32].hex()
    offset += 32

    cid_len = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    if offset + cid_len > len(data):
        return None
    ipfs_cid = data[offset:offset + cid_len].decode("utf-8", errors="replace")
    offset += cid_len

    if offset + 16 > len(data):
        return None
    timestamp = struct.unpack_from("<q", data, offset)[0]
    offset += 8
    verification_count = struct.unpack_from("<Q", data, offset)[0]

    return {
        "owner": owner,
        "sha256_hash": sha256_hash,
        "ipfs_cid": ipfs_cid,
        "timestamp": timestamp,
        "verification_count": verification_count,
    }


async def register_media(
    sha256_hash: str,
    ipfs_cid: str,
    wallet_address: str,
    tx_signature: str,
) -> str:
    """
    Verify that the user's wallet successfully submitted a register_media transaction.
    Returns the confirmed transaction signature.

    In dev mode (SOLANA_PROGRAM_ID unset) returns a mock signature so the
    rest of the pipeline stays testable without a live cluster.
    """
    if not settings.solana_program_id:
        mock_sig = f"MOCK_{sha256_hash[:16]}_{int(datetime.now(timezone.utc).timestamp())}"
        return mock_sig

    result = await _rpc(
        "getTransaction",
        [
            tx_signature,
            {
                "encoding": "json",
                "commitment": "confirmed",
                "maxSupportedTransactionVersion": 0,
            },
        ],
    )
    tx_data = result.get("result")
    if not tx_data:
        raise ValueError("Transaction not confirmed on-chain")

    # Verify the transaction called our program
    account_keys = (
        tx_data.get("transaction", {})
        .get("message", {})
        .get("accountKeys", [])
    )
    if settings.solana_program_id not in account_keys:
        raise ValueError("Transaction did not call the proof_layer program")

    return tx_signature


async def get_media_record(sha256_hash: str) -> dict | None:
    """
    Fetch and decode the on-chain MediaRecord PDA for the given SHA256 hash.
    Returns the decoded fields or None if the account does not exist.
    """
    if not settings.solana_program_id:
        return None

    try:
        pda_address, _ = _derive_media_pda(sha256_hash, settings.solana_program_id)
    except Exception:
        return None

    result = await _rpc(
        "getAccountInfo",
        [pda_address, {"encoding": "base64", "commitment": "confirmed"}],
    )
    account = result.get("result", {}).get("value")
    if not account:
        return None

    try:
        raw = base64.b64decode(account["data"][0])
        return _decode_media_record(raw)
    except Exception:
        return None


async def get_slot_timestamp() -> int:
    """Return current Solana cluster time (unix seconds)."""
    result = await _rpc("getBlockTime", [await _get_current_slot()])
    return result.get("result", int(datetime.now(timezone.utc).timestamp()))


async def _get_current_slot() -> int:
    result = await _rpc("getSlot", [])
    return result.get("result", 0)
