from contextlib import asynccontextmanager
import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.clients.gamma import GammaClient
from app.clients.clob import CLOBClient
from app.config import settings
from app.engine.scanner import refresh_scanner
from app.routes.scanner import router as scanner_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    gamma_client = GammaClient()
    clob_client = CLOBClient()

    app.state.gamma_client = gamma_client
    app.state.clob_client = clob_client
    app.state.scanner_results = []

    async def run_scan():
        try:
            results = await refresh_scanner(gamma_client, clob_client)
            app.state.scanner_results = results
        except Exception as e:
            logger.error(f"Scanner refresh failed: {e}")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_scan, "interval", seconds=settings.poll_interval_seconds)
    scheduler.start()
    app.state.scheduler = scheduler

    # Fire initial scan in background so server starts accepting requests immediately
    logger.info("Server starting — initial scan running in background...")
    asyncio.create_task(run_scan())

    yield

    scheduler.shutdown()
    await gamma_client.close()
    await clob_client.close()
    logger.info("Backend shut down")


app = FastAPI(title="Polymarket NO Scanner", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scanner_router)

# Serve frontend static files in production
# In Docker: /frontend/dist. Locally: ../frontend/dist relative to backend/
import os
_static_override = os.environ.get("STATIC_DIR")
STATIC_DIR = Path(_static_override) if _static_override else Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the React SPA for any non-API route."""
        file = STATIC_DIR / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(STATIC_DIR / "index.html")
