from typing import Dict, Any

from httpx import AsyncClient, Response, HTTPStatusError
from fastapi import UploadFile

from src.constants import configs
from src.utils.logging import logger

class PlateRecognizerService:
    """เชื่อมต่อกับ AI สำหรับอ่านป้ายทะเบียน"""
    
    def __init__(self):
        self.client = AsyncClient(base_url=configs.PLATE_RECOG_BASE_URL, timeout=60.0)
    
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
        ส่ง cropped plate ไปให้ AI ประมวลผล
        ใช้ /process endpoint (AI จะ detect plate อีกรอบ แต่เนื่องจากเป็น plate crop แล้ว จะเร็วและแม่น)
        
        Args:
            upload_file: ไฟล์รูปป้ายทะเบียนที่ crop แล้ว
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

    async def close(self):
        """ปิด HTTP client"""
        await self.client.aclose()