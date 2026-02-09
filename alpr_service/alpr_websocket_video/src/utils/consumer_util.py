import os
import asyncio
from io import BytesIO

import cv2
import numpy as np
from fastapi import UploadFile

from .logging import logger
from src.models.tracker import VideoPlateTracker, VideoCarTracker
from src.constants import configs

def process_frame(frame_bytes: bytes, tracker):
  """Process frame with any tracker (VideoPlateTracker or VideoCarTracker)"""
  image = cv2.imdecode(np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
  if image is None:
    return None, None

  result = tracker.process_frame(image)
  return result

async def process_frame_async(frame_bytes: bytes, tracker):
  """Async wrapper for process_frame"""
  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, process_frame, frame_bytes, tracker)
  return result

def numpy_to_upload_file(image: np.ndarray, filename: str = "image.jpg"):
  success, encoded_image = cv2.imencode('.jpg', image)
  if not success:
    logger.error("Failed to encode the NumPy array as an image.")
    return None
  image_stream = BytesIO(encoded_image.tobytes())
  return UploadFile(file=image_stream, filename=filename)

async def numpy_to_upload_file_async(image: np.ndarray, filename: str = "image.jpg"):
  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, numpy_to_upload_file, image, filename)
  return result

def save_image(image: np.ndarray, filename: str):
  success = cv2.imwrite(os.path.join(configs.IMAGES_PATH, filename), image)
  if not success:
    raise IOError(f"Failed to save image to {filename}")

async def save_image_async(image: np.ndarray, filename: str):
  loop = asyncio.get_event_loop()
  await loop.run_in_executor(None, save_image, image, filename)

async def encode_image_async(image, format=".jpg"):
  loop = asyncio.get_running_loop()
  return await loop.run_in_executor(None, cv2.imencode, format, image)

async def encode_image_to_byte(image: np.ndarray):
  success, encoded_image = await encode_image_async(image)
  if success:
    return encoded_image.tobytes()
  else:
    return False

def resize_image(image: np.ndarray, max_width: int = 640):
  """Resize image to reduce resolution while maintaining aspect ratio"""
  height, width = image.shape[:2]
  if width > max_width:
    ratio = max_width / width
    new_width = max_width
    new_height = int(height * ratio)
    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    return resized
  return image

async def resize_image_async(image: np.ndarray, max_width: int = 640):
  """Async wrapper for resize_image"""
  loop = asyncio.get_event_loop()
  result = await loop.run_in_executor(None, resize_image, image, max_width)
  return result
