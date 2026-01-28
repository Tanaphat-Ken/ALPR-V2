import os
import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.constants import configs
from src.handlers import rtsp_handler
from src.utils.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler"""
    # Startup
    logger.info("=== ALPR RTSP Service Starting ===")
    await rtsp_handler.startup_rtsp()
    yield
    # Shutdown
    logger.info("=== ALPR RTSP Service Stopping ===")
    await rtsp_handler.shutdown_rtsp()


app = FastAPI(title="ALPR RTSP Service", lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=configs.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=configs.ALLOW_METHODS,
    allow_headers=configs.ALLOW_HEADERS,
)

# Include routers
app.include_router(rtsp_handler.router, prefix="/api/v1", tags=["rtsp"])

# Ensure static directory exists
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

# Serve static files (Web Viewer)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Serve Web Viewer"""
    viewer_path = Path("static/viewer.html")
    if viewer_path.exists():
        return FileResponse("static/viewer.html")
    else:
        return {"message": "ALPR RTSP Service is running. Web viewer not found at /static/viewer.html"}


@app.get("/readyz")
async def readyz():
    """Health check"""
    return {"message": "RTSP service is ready!"}





if __name__ == "__main__":
    is_reload = configs.ENVIRONMENT == 'dev'
    uvicorn.run(
        "main:app",
        host=configs.HOST,
        port=configs.PORT,
        log_level="info",
        reload=is_reload
    )
