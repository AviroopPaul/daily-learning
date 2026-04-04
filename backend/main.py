import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.scheduler import start_scheduler, stop_scheduler
from backend.routers import topics, subscriptions, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs("data", exist_ok=True)
    init_db()
    logger.info("Database initialized")

    start_scheduler()

    yield

    # Shutdown
    stop_scheduler()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="SysDesign Daily",
    description="Daily system design topics — one concept a day",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(topics.router)
app.include_router(subscriptions.router)
app.include_router(admin.router)


# Health check
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "sysdesign-daily"}


# Serve React SPA — static files + fallback
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Serve static files if they exist, otherwise return index.html (SPA routing)
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    logger.warning(f"Static dir not found at {STATIC_DIR} — frontend not served")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8080, reload=True)
