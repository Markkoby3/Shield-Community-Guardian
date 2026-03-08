import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.api.routes import router, limiter
from backend.services.rag import init_rag
from backend.db.database import get_conn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    logger.info("Starting Community Guardian...")
    get_conn()          # initialise DB + schema
    try:
        init_rag()
        logger.info("RAG chain ready")
    except Exception as e:
        logger.error("RAG initialization failed: %s", e, exc_info=True)
        # App still starts — endpoints will use fallback digest mode
    yield
    # ── Shutdown ──
    logger.info("Shutting down Community Guardian")


app = FastAPI(
    title="Community Guardian",
    description="RAG-powered community safety alert system",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s: %s", request.url, exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(router, prefix="/api/v1")

# Serve frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", response_class=FileResponse)
    def frontend():
        return str(FRONTEND_DIR / "index.html")
else:
    @app.get("/")
    def root():
        return {"service": "Community Guardian", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"status": "ok"}
