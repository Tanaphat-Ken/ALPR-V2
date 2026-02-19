import uuid
import base64
import asyncio
from datetime import datetime

import cv2
import numpy as np
from fastapi import WebSocket

from .logging import logger
from .consumer_util import *
from src.models.tracker import VideoPlateTracker
from src.services.plate_recognizer import PlateRecognizerService
from src.services.database import commit_websocket_log, devalue_video_quota
from src.constants import errors

plate_recognizer = PlateRecognizerService()

# Global duplicate detection (last seen plates with timestamps)
recent_plates = {}  # {plate_text: timestamp}
DUPLICATE_THRESHOLD = 3.0  # seconds - ignore same plate within this time

async def consume(websocket: WebSocket, token: str, user_id: str, client_queue: asyncio.Queue, video_tracker: VideoPlateTracker):
  frame_counter = 0 # for debugging
  try:
    while True:
      frame_bytes = await client_queue.get()
      logger.info(f"Processing frame #{frame_counter}, size: {len(frame_bytes)} bytes, queue remaining: {client_queue.qsize()}")

      # Send progress update to frontend
      try:
        await websocket.send_json({
          "status": "progress",
          "frame_number": frame_counter,
          "queue_size": client_queue.qsize()
        })
      except:
        pass  # Continue processing even if can't send progress

      # Decode frame_bytes to get full image
      full_image = cv2.imdecode(np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)

      # process_frame_async now returns (plate_crop, plate_detected_flag)
      plate_crop, plate_detected = await process_frame_async(frame_bytes, video_tracker)

      logger.info(f"Frame #{frame_counter}: plate_detected={plate_detected is not None}")

      if plate_crop is not None and plate_detected:
        logger.info(f"Frame #{frame_counter}: Sending cropped plate to plate_recognizer")
        try:
          image_file = await numpy_to_upload_file_async(plate_crop)
          # Call /process/from-plate-crop endpoint (skip PlateDetector step)
          response = await plate_recognizer.process_plate_crop(image_file)
          
          # Text-based duplicate detection
          response_data = response.json()
          plate_text = response_data.get('plate_id', '')
          current_time = datetime.now().timestamp()
          
          # Check if this plate was seen recently
          if plate_text and plate_text in recent_plates:
            time_diff = current_time - recent_plates[plate_text]
            if time_diff < DUPLICATE_THRESHOLD:
              logger.info(f"⏭️  Skipping duplicate plate: {plate_text} (seen {time_diff:.1f}s ago)")
              frame_counter += 1
              continue
          
          # Update recent plates tracking
          if plate_text:
            recent_plates[plate_text] = current_time
            # Clean up old entries (older than 10 seconds)
            old_keys = [k for k, v in recent_plates.items() if current_time - v >= 10.0]
            for k in old_keys:
              del recent_plates[k]
          
          filename = f"{uuid.uuid4()}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"

          await save_image_async(plate_crop, filename)
          await commit_websocket_log(response_data, token, user_id, filename)
          await devalue_video_quota(user_id)

          result_data = response.json()
          result_data['filename'] = filename

          # Send resized full image as base64 for web display (to see full context)
          if full_image is not None:
            resized_image = await resize_image_async(full_image, max_width=480)
            image_bytes = await encode_image_to_byte(resized_image)
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            result_data['image'] = f"data:image/jpeg;base64,{image_base64}"

          # Send plate crop image as base64 for web display
          plate_crop_bytes = await encode_image_to_byte(plate_crop)
          plate_crop_base64 = base64.b64encode(plate_crop_bytes).decode('utf-8')
          result_data['plateCropImage'] = f"data:image/jpeg;base64,{plate_crop_base64}"

          try:
            await websocket.send_json(result_data)
            logger.info(f"Frame #{frame_counter}: Response sent successfully")
          except Exception as ws_err:
            logger.warning(f"Failed to send response (websocket closed): {ws_err}")
            break

        except ValueError as e:
          logger.error(str(e))
          try:
            await websocket.send_text(f"Error: {str(e)}")
          except:
            break

        except Exception as e:
          logger.error(str(e))
          try:
            await websocket.send_text(errors.SERVER_ERROR)
          except:
            break
      else:
        logger.info(f"Frame #{frame_counter}: No plate finalized yet, skipping")

      frame_counter += 1
      client_queue.task_done()  # Mark frame as fully processed

  except asyncio.CancelledError:
    logger.info("Consumer task cancelled - cleaning up")
    raise  # Re-raise to properly cleanup
  
  except Exception as e:
    logger.error(f"Unexpected error in consumer: {e}")
    raise