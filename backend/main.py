from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import traceback
import logging
import httpx

from config import settings
from utils.db import init_db, AsyncSessionLocal
from sqlalchemy import text
from routes.upload import router as upload_router
from routes.register import router as register_router
from routes.verify import router as verify_router
from routes.media import router as media_router
from routes.history import router as history_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)


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

@app.exception_handler(Exception)
async def _debug_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"\n=== UNHANDLED EXCEPTION ===\n{tb}=== END ===\n")
    return JSONResponse(status_code=500, content={"detail": str(exc), "type": type(exc).__name__})


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


@app.get("/health/detail")
async def health_detail():
    """Check every downstream dependency — open this in your browser to diagnose 500s."""
    result = {}

    # PostgreSQL
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        result["database"] = "ok"
    except Exception as exc:
        result["database"] = f"ERROR: {exc}"

    # Redis
    try:
        from utils.cache import _get_client
        client = _get_client()
        if client is None:
            result["redis"] = "skipped (redis library not installed)"
        else:
            await client.ping()
            result["redis"] = "ok"
    except Exception as exc:
        result["redis"] = f"ERROR: {exc}"

    # AI service
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{settings.ai_service_url}/health")
            result["ai_service"] = "ok" if r.status_code == 200 else f"HTTP {r.status_code}"
    except Exception as exc:
        result["ai_service"] = f"ERROR (is ai service running on port 8001?): {exc}"

    # Config snapshot
    result["config"] = {
        "solana_program_id": settings.solana_program_id or "(empty — mock mode)",
        "ai_service_url": settings.ai_service_url,
        "pinata_configured": bool(settings.pinata_jwt or settings.pinata_api_key),
    }

    result["overall"] = "ok" if all(
        v == "ok" for k, v in result.items() if k not in ("config", "redis", "overall")
    ) else "degraded"

    return result
