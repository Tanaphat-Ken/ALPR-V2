import signal
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from src.constants import configs
from src.handlers import video
from src.utils.logging import logger
from src.utils.cleanup import shutdown_tasks

@asynccontextmanager
async def lifespan(app: FastAPI):
  # Startup
  logger.info("Application startup complete")
  yield
  # Shutdown
  await shutdown_tasks()
  logger.info("Application shutdown complete")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
  CORSMiddleware,
  allow_origins=configs.ALLOW_ORIGINS,
  allow_credentials=True,
  allow_methods=configs.ALLOW_METHODS,
  allow_headers=configs.ALLOW_HEADERS,
)
shutdown_event = asyncio.Event()

def handle_sigterm(signum, frame):
  logger.info(f"Received signal {signum}. Initiating shutdown.")
  shutdown_event.set()

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

@app.websocket("/{token}")
async def websocket_route(websocket: WebSocket, token: str):
  await video.websocket_endpoint(websocket, token)

@app.get("/readyz")
async def readyz():
  return { "message": "service is ready!" }

if __name__ == "__main__":
  is_reload = configs.ENVIRONMENT == 'dev'
  # Use Config object to properly set ws_max_size even with reload
  config = uvicorn.Config(
    "main:app",
    host=configs.HOST,
    port=configs.PORT,
    log_level="info",
    reload=is_reload,
    ws_max_size=configs.WS_MAX_SIZE  # 5MB to support full frame images
  )
  server = uvicorn.Server(config)
  server.run() 