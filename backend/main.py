from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from utils.db import init_db
from routes.upload import router as upload_router
from routes.register import router as register_router
from routes.verify import router as verify_router
from routes.media import router as media_router
from routes.history import router as history_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Decentralized media provenance and deepfake verification backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, tags=["media"])
app.include_router(register_router, tags=["provenance"])
app.include_router(verify_router, tags=["verification"])
app.include_router(media_router, tags=["media"])
app.include_router(history_router, tags=["history"])


@app.get("/health")
async def health():
    return {"status": "ok"}
