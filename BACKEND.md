# BACKEND CONTEXT — ProofLayer

## Overview

FastAPI backend for ProofLayer.

Responsibilities:
- image uploads
- hashing
- IPFS integration
- orchestration
- AI service communication
- Solana communication

---

# Stack

- FastAPI
- Python
- PostgreSQL
- Redis
- httpx

---

# Core Responsibilities

## Upload media
Receive image/video uploads.

---

## Generate SHA256 hash

Used for:
- exact identity
- provenance

---

## Upload media to IPFS

Use:
- Pinata API

Returns:
- CID

---

## Call Solana services

Store:
- hash
- CID
- timestamp

---

## Verification orchestration

Workflow:
1. receive suspicious image
2. generate hashes
3. call AI services
4. aggregate results
5. return authenticity score

---

# Endpoints

## POST /upload

Returns:
{
  "hash": "...",
  "cid": "..."
}

---

## POST /register

Registers media provenance on Solana.

---

## POST /verify

Returns:
{
  "similarity": 87,
  "deepfake_probability": 0.72,
  "status": "Likely Manipulated"
}

---

# Folder Structure

backend/
│
├── routes/
├── services/
├── utils/
├── models/
└── main.py

---

# Services

## hashing.py
SHA256 generation.

---

## ipfs.py
Pinata upload integration.

---

## solana.py
Solana transaction handling.

---

## verification.py
Verification orchestration.

---

# Important

Keep architecture simple.
Prioritize:
- working APIs
- reliability
- fast integration
- demo readiness