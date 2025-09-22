import uuid
import base64
import asyncio
from datetime import datetime

from fastapi import WebSocket

from .logging import logger
from .consumer_util import *
from src.models.tracker import VideoCarTracker
from src.services.plate_recognizer import PlateRecognizerService
from src.services.database import commit_websocket_log
from src.constants import errors

plate_recognizer = PlateRecognizerService()

async def consume(websocket: WebSocket, token: str, user_id: str, client_queue: asyncio.Queue, video_tracker: VideoCarTracker):
  frame_counter = 0 # for debuggin
  try:
    while True:
      frame_bytes = await client_queue.get()
      car_image, bbox = await process_frame_async(frame_bytes, video_tracker)

      if car_image is not None:
        try:
          image_file = await numpy_to_upload_file_async(car_image)
          response = await plate_recognizer.process_image(bbox, image_file)
          filename = f"{uuid.uuid4()}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"

          await save_image_async(car_image, filename)
          await commit_websocket_log(response.json(), token, user_id, filename)

          result_data = response.json()
          image_bytes = await encode_image_to_byte(car_image)
          image_base64 = base64.b64encode(image_bytes).decode('utf-8')
          result_data['image'] = f"data:image/jpeg;base64,{image_base64}" 

          await websocket.send_json(result_data)
          
        except ValueError as e:
          logger.error(str(e))
          await websocket.send_text(f"Error: {str(e)}")

        except Exception as e:
          logger.error(str(e))
          await websocket.send_text(errors.SERVER_ERROR)

      logger.info(frame_counter)
      frame_counter += 1

  except asyncio.CancelledError:
    logger.error("Processing task cancelled.")