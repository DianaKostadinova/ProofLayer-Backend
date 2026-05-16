# ProofLayer — Solana Media Provenance & Deepfake Verification Platform

## Project Vision

ProofLayer is a decentralized media authenticity and provenance platform built on Solana.

The platform allows users to:
- Register original media on-chain
- Verify authenticity of images/videos
- Detect manipulated or deepfake-derived content
- Track provenance history of digital media
- Provide trust scoring for media authenticity

This is NOT just an AI deepfake detector.

The core value is:
> decentralized, immutable media provenance infrastructure powered by Solana.

AI is used as an assisting verification layer.

---

# Core Problem

AI-generated and manipulated media is making digital content increasingly untrustworthy.

Current systems are:
- centralized
- forgeable
- editable
- lack transparent provenance

Users cannot reliably verify:
- origin
- ownership
- timestamp authenticity
- manipulation history

---

# Solution

ProofLayer creates a decentralized authenticity registry for digital media.

Every uploaded media file:
- gets fingerprinted
- signed by wallet owner
- timestamped
- registered on Solana
- stored on decentralized storage

Verification combines:
- blockchain provenance
- cryptographic identity
- perceptual similarity
- AI-assisted manipulation detection

---

# Full System Architecture

```text
                    ┌──────────────────────┐
                    │      FRONTEND        │
                    │ Next.js Web Platform │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      API GATEWAY     │
                    │ Auth / Routing / JWT │
                    └──────────┬───────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼

┌────────────────┐  ┌────────────────┐  ┌────────────────────┐
│ MEDIA SERVICE  │  │VERIFY SERVICE  │  │ USER/IDENTITY SVC  │
│ Upload         │  │ Similarity     │  │ Wallet auth        │
│ IPFS storage   │  │ AI detection   │  │ Reputation         │
│ Metadata       │  │ Trust scoring  │  │ Roles              │
└──────┬─────────┘  └────────┬───────┘  └─────────┬──────────┘
       │                     │                    │
       ▼                     ▼                    ▼

┌─────────────────────────────────────────────────────────────┐
│                    AI/ML PIPELINE                           │
│ - SHA256 hashing                                            │
│ - pHash generation                                          │
│ - CLIP embeddings                                           │
│ - Deepfake detection models                                 │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼

┌─────────────────────────────────────────────────────────────┐
│                    VECTOR DATABASE                          │
│ Pinecone / FAISS                                            │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼

┌─────────────────────────────────────────────────────────────┐
│                     SOLANA LAYER                            │
│ Anchor Program                                               │
│ - Provenance registry                                        │
│ - Ownership                                                  │
│ - Hash records                                               │
│ - Verification events                                        │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼

┌─────────────────────────────────────────────────────────────┐
│                     STORAGE LAYER                           │
│ IPFS / Arweave                                               │
└─────────────────────────────────────────────────────────────┘