from typing import Dict, Any

import httpx
from httpx import AsyncClient, Response, HTTPStatusError
from fastapi import UploadFile

from src.constants import configs
from src.utils.logging import logger

class PlateRecognizerService:
    """เชื่อมต่อกับ AI สำหรับอ่านป้ายทะเบียน"""
    
    def __init__(self):
        # timeout=10s: ป้องกัน httpx รอนานจน nginx timeout ก่อน
        # connect_timeout=5s: fail fast ถ้า service ไม่ตอบ
        self.client = AsyncClient(
            base_url=configs.PLATE_RECOG_BASE_URL,
            timeout=httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
        )
    
    async def process_image(self, upload_file: UploadFile, headers: Dict[str, Any] = None) -> Response:
        """
        ส่งรูปเต็มไปให้ AI ประมวลผล (AI จะ detect plate เอง)
        
        Args:
            upload_file: ไฟล์รูป
            headers: HTTP headers (optional)
        """
        files = {
            "file": (upload_file.filename, await upload_file.read(), upload_file.content_type)
        }

        try:
            response = await self.client.post("/image/process", files=files, headers=headers)
            response.raise_for_status()
            return response
        except HTTPStatusError as e:
            logger.error(f"Plate recognizer HTTP error: {e}")
            if e.response is not None:
                raise ValueError(e.response)
            raise ValueError("AI service error")
    
    async def process_plate_crop(self, upload_file: UploadFile, headers: Dict[str, Any] = None) -> Response:
        """
        ส่ง cropped plate ไปให้ AI ประมวลผล (ข้าม PlateDetector step)
        ใช้ /image/process/from-plate-crop endpoint เพื่อความเร็วและแม่นยำ
        
        Args:
            upload_file: ไฟล์รูปป้ายทะเบียนที่ crop แล้ว (จาก VideoPlateTracker)
            headers: HTTP headers (optional)
        """
        files = {
            "file": (upload_file.filename, await upload_file.read(), upload_file.content_type)
        }

        try:
            # เรียก endpoint ที่ข้าม PlateDetector (เพราะเรา detect แล้วด้วย VideoPlateTracker)
            response = await self.client.post("/image/process/from-plate-crop", files=files, headers=headers)
            response.raise_for_status()
            return response
        except HTTPStatusError as e:
            logger.error(f"Plate recognizer HTTP error: {e}")
            if e.response is not None:
                raise ValueError(e.response)
            raise ValueError("AI service error")

    async def close(self):
        """ปิด HTTP client"""
        await self.client.aclose()