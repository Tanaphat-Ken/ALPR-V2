import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect

from src.constants import configs, errors
from src.utils import logger, validator, consumer
from src.models import VideoPlateTracker
from src.services.database import get_user_id_with_token

async def websocket_endpoint(websocket: WebSocket, token: str):
  try:
    user_id = await get_user_id_with_token(token)
  except ValueError as ve:
    logger.error(f"Token validation failed for {token}: {ve.args[0]}")
    await websocket.close(code=4001, reason=f"{ve.args[0]}")
    return
  except Exception as e:
    logger.error(f"Unexpected error in token validation for {token}: {str(e)}")
    await websocket.close(code=1011, reason="Internal server error")
    return

  await websocket.accept()

  video_tracker = VideoPlateTracker()  # Use PlateDetector instead of car detection
  client_queue = asyncio.Queue()
  consumer_process = asyncio.create_task(consumer.consume(websocket, token, user_id, client_queue, video_tracker))

  try:
    while True:
      frame_bytes = await websocket.receive_bytes()

      # Check if this is a blank finalization frame (< 3KB)
      # Normal video frames are typically 50KB-500KB even with compression
      # Blank 100x100 frame at quality 0.1 is usually < 2KB
      if len(frame_bytes) < 3000:
        logger.info(f"Received blank frame ({len(frame_bytes)} bytes), finalizing video processing")
        await websocket.send_json({"status": "processing", "message": "Video upload complete, processing frames..."})
        break  # Exit receive loop, wait for queue to finish

      if len(frame_bytes) > configs.MAX_FILE_SIZE:
        await websocket.send_text(json.dumps(errors.FILE_TOO_LARGE))
        continue

      if not validator.is_image(frame_bytes):
        await websocket.send_text(json.dumps(errors.INVALID_FORMAT))
        continue
        
      await client_queue.put(frame_bytes)
  
  except WebSocketDisconnect as e:
    logger.info(f"WebSocket disconnected with code: {e.code} and reason: {e.reason}")

  except Exception as e:
    logger.error(f"Unexpected error in WebSocket: {e}")

  finally:
    # Wait for queue to be fully processed before closing
    logger.info(f"Waiting for {client_queue.qsize()} remaining frames to process")
    
    # Wait up to 120 seconds for queue to empty
    wait_time = 0
    while not client_queue.empty() and wait_time < 120:
      await asyncio.sleep(1)
      wait_time += 1
      if wait_time % 10 == 0:
        logger.info(f"Still processing... {client_queue.qsize()} frames remaining")
    
    # Send completion message before canceling consumer
    try:
      await websocket.send_json({"status": "completed", "message": "All frames processed"})
      logger.info("Sent completion message to client")
    except:
      pass
    
    # Cancel consumer task and wait for cleanup
    consumer_process.cancel()
    try:
      await consumer_process
    except asyncio.CancelledError:
      pass
    
    # Close websocket if still open
    try:
      await websocket.close()
    except:
      pass
