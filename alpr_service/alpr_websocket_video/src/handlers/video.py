import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect

from src.constants import configs, errors
from src.utils import logger, validator, consumer
from src.models import VideoCarTracker
from src.services.database import get_user_id_with_token

async def websocket_endpoint(websocket: WebSocket, token: str):
  try:
    user_id = await get_user_id_with_token(token)
  except ValueError as ve:
    await websocket.close(code=4001, reason=f"{ve.args[0]}")
    return
  except Exception as e:
    await websocket.close(code=1011, reason="Internal server error")
    return
  
  await websocket.accept()

  video_tracker = VideoCarTracker()
  client_queue = asyncio.Queue()
  consumer_process = asyncio.create_task(consumer.consume(websocket, token, user_id, client_queue, video_tracker))

  try:
    while True:
      frame_bytes = await websocket.receive_bytes()

      if len(frame_bytes) > configs.MAX_FILE_SIZE:
        await websocket.send_text(json.dumps(errors.FILE_TOO_LARGE))
        continue

      if not validator.is_image(frame_bytes):
        await websocket.send_text(json.dumps(errors.INVALID_FORMAT))
        continue
        
      await client_queue.put(frame_bytes)
  
  except WebSocketDisconnect as e:
    logger.info(f"WebSocket disconnected with code: {e.code} and reason: {e.reason}")
    await websocket.send_text(json.dumps(errors.DISCONNECT))

  except Exception as e:
    logger.error(f"Unexpected error in WebSocket: {e}")
    await websocket.send_text(json.dumps(errors.DISCONNECT))

  finally:
    consumer_process.cancel()
    await websocket.close()
