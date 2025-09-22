import signal
import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.constants import configs
from src.handlers import video
from src.utils.logging import logger
from src.utils.cleanup import shutdown_tasks

app = FastAPI()

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

app.add_api_websocket_route("/video/{token}", video.websocket_endpoint)

@app.get("/readyz")
async def readyz():
  return { "message": "service is ready!" }

@app.on_event("shutdown")
async def shutdown():
  await shutdown_tasks()

if __name__ == "__main__":
  is_reload = configs.ENVIRONMENT == 'dev'
  uvicorn.run("main:app", host=configs.HOST, port=configs.PORT, log_level="info", reload=is_reload) 