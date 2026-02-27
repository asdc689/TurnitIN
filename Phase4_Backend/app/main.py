import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import engine, Base
from app.api.auth import router as auth_router
from app.api.submissions import router as submissions_router

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.DEBUG if not settings.is_production else logging.INFO,
    format  = "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(
    key_func       = get_remote_address,
    default_limits = [f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]
)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    Startup:  creates DB tables, ensures MinIO bucket exists.
    Shutdown: disposes DB connection pool.
    """
    logger.info("Starting up %s [env=%s]", settings.APP_NAME, settings.APP_ENV)

    # Create all tables (no-op if they already exist)
    # In production use Alembic migrations instead
    async with engine.begin() as conn:
        # Import all models so Base knows about them
        import app.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created")

    # Ensure MinIO bucket exists (safe to call every time)
    try:
        from app.services.file_service import ensure_bucket_exists
        ensure_bucket_exists()
    except Exception as e:
        logger.warning("Storage bucket check failed (MinIO may not be running): %s", e)

    yield

    # Shutdown
    logger.info("Shutting down — disposing DB engine")
    await engine.dispose()


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title       = settings.APP_NAME,
    description = "AI-powered plagiarism detection for text and code submissions.",
    version     = "1.0.0",
    docs_url    = "/docs"  if not settings.is_production else None,
    redoc_url   = "/redoc" if not settings.is_production else None,
    lifespan    = lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = settings.allowed_origins_list,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Global Exception Handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s: %s", request.method, request.url, exc)
    return JSONResponse(
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
        content     = {"detail": "An internal server error occurred. Please try again later."},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth_router,        prefix=API_PREFIX)
app.include_router(submissions_router, prefix=API_PREFIX)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status":  "ok",
        "app":     settings.APP_NAME,
        "env":     settings.APP_ENV,
        "version": "1.0.0",
    }


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs":    "/docs",
        "health":  "/health",
    }