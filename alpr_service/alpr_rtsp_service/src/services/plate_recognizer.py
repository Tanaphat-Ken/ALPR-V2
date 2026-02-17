import httpx
from typing import Optional
from fastapi import UploadFile

from src.constants import configs
from src.utils.logging import logger

class PlateRecognizerService:
    """เชื่อมต่อกับ AI สำหรับอ่านป้ายทะเบียน"""
    
    def __init__(self):
        self.url = configs.PLATE_RECOGNIZER_URL
        self.timeout = 30.0
    
    async def process_image(self, bbox: list, image_file: UploadFile) -> httpx.Response:
        """
        ส่งรูปรถไปให้ AI ประมวลผล
        
        Args:
            bbox: ตำแหน่งรถ [x1, y1, x2, y2]
            image_file: ไฟล์รูปรถ
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {
                    "file": (image_file.filename, image_file.file, "image/jpeg")
                }
                data = {
                    "car_bbox": str(bbox.tolist() if hasattr(bbox, 'tolist') else list(bbox))
                }
                
                response = await client.post(
                    f"{self.url}/skip/car",
                    files=files,
                    data=data
                )
                
                response.raise_for_status()
                return response
                
        except httpx.TimeoutException:
            logger.error("Plate recognizer timeout")
            raise ValueError("AI service timeout")
        except httpx.HTTPStatusError as e:
            logger.error(f"Plate recognizer HTTP error: {e}")
            raise ValueError(f"AI service error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Plate recognizer error: {e}")
            raise ValueError(f"AI service error: {str(e)}")
