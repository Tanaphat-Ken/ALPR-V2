from typing import Dict, Any

from httpx import AsyncClient, Response, HTTPStatusError
from fastapi import UploadFile

from src.constants import configs

class PlateRecognizerService:
  def __init__(self):
    self.client = AsyncClient(base_url=configs.PLATE_RECOG_BASE_URL, timeout=60.0)

  async def process_image(self, upload_file: UploadFile, headers: Dict[str, Any] = None) -> Response:
    # Send full frame to plate_recognizer /image/process endpoint
    # plate_recognizer will detect license plate from full image
    files = {
      "file": (upload_file.filename, await upload_file.read(), upload_file.content_type)
    }

    try:
      response = await self.client.post("/image/process", files=files, headers=headers)
      response.raise_for_status()
      return response
    except HTTPStatusError as e:
      if e.response is not None:
        raise ValueError(e.response)

  async def process_plate_crop(self, upload_file: UploadFile, headers: Dict[str, Any] = None) -> Response:
    # Send cropped plate to plate_recognizer /process/from-plate-crop endpoint
    # plate_recognizer will skip PlateDetector step and process directly
    files = {
      "file": (upload_file.filename, await upload_file.read(), upload_file.content_type)
    }

    try:
      response = await self.client.post("/image/process/from-plate-crop", files=files, headers=headers)
      response.raise_for_status()
      return response
    except HTTPStatusError as e:
      if e.response is not None:
        raise ValueError(e.response)

  async def close(self):
    await self.client.aclose()

