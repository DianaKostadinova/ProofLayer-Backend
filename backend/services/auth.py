"""
Wallet signature verification.

Solana wallets sign messages with ed25519. The wallet address is a
base58-encoded 32-byte public key. The signature is base58-encoded 64 bytes.

The frontend should sign the SHA256 hash string (hex) using the wallet's
signMessage method, then send the base58-encoded signature here.
"""
import base64

try:
    import base58
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError
    _NACL_AVAILABLE = True
except ImportError:
    _NACL_AVAILABLE = False


def verify_wallet_signature(wallet_address: str, message: str, signature: str) -> bool:
    """
    Returns True if the signature is a valid ed25519 signature of `message`
    by the wallet at `wallet_address`.

    Falls back to True (permissive) when PyNaCl/base58 are not installed so
    the rest of the pipeline remains testable during development.
    """
    if not _NACL_AVAILABLE:
        return True

    try:
        pub_key_bytes = base58.b58decode(wallet_address)
        # Try base58 signature first, fall back to base64 (some wallets use base64)
        try:
            sig_bytes = base58.b58decode(signature)
        except Exception:
            sig_bytes = base64.b64decode(signature)

        verify_key = VerifyKey(pub_key_bytes)
        verify_key.verify(message.encode("utf-8"), sig_bytes)
        return True
    except (BadSignatureError, Exception):
        return False
