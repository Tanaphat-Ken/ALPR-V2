from typing import Dict, Any

from httpx import AsyncClient, Response, HTTPStatusError
from fastapi import UploadFile
import numpy as np

from src.constants import configs

class PlateRecognizerService:
  def __init__(self):
    self.client = AsyncClient(base_url=configs.PLATE_RECOG_BASE_URL, timeout=60.0)

  async def process_image(self, car_bbox: np.ndarray, upload_file: UploadFile, headers: Dict[str, Any] = None) -> Response:
    data = { "car_bbox": car_bbox.tolist() }
    files = { "file": (upload_file.filename, await upload_file.read(), upload_file.content_type) }

    try:
      response = await self.client.post("/image/process/skip/car", data=data, files=files, headers=headers)
      response.raise_for_status()
      return response
    except HTTPStatusError as e:
      if e.response is not None:
        raise ValueError(e.response)

  async def close(self):
    await self.client.aclose()

