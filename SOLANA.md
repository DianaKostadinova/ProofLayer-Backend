# SOLANA CONTEXT — ProofLayer

## Overview

Solana provenance registry for ProofLayer.

Purpose:
- immutable authenticity records
- ownership proof
- timestamp verification
- decentralized provenance

Blockchain stores ONLY metadata.

NOT images/videos.

---

# Stack

- Solana
- Anchor
- Rust
- Phantom Wallet

---

# Smart Contract Responsibilities

Store:
- SHA256 hash
- IPFS CID
- owner wallet
- timestamp

---

# Account Structure

```rust
pub struct MediaRecord {
    pub owner: Pubkey,
    pub sha256_hash: [u8; 32],
    pub ipfs_cid: String,
    pub timestamp: i64,
}