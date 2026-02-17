"""
Database Service - บันทึกข้อมูลการตรวจจับรถ
MVP: เตรียมโค้ดไว้ แต่ยังไม่ enable
"""
import os
from datetime import datetime
from typing import Optional, Dict, Any

from src.utils.logging import logger


class DatabaseService:
    """
    จัดการการบันทึกข้อมูลลงฐานข้อมูล
    
    MVP Approach:
    - Phase 1: Log to file only (ตอนนี้)
    - Phase 2: Save to database (เมื่อพร้อม)
    """
    
    def __init__(self, enabled: bool = False):
        """
        Args:
            enabled: เปิด/ปิด การบันทึกลง database
                     False = MVP (แค่ log)
                     True = บันทึกจริง
        """
        self.enabled = enabled
        self.log_file = "images_logs/detections.log"
        
        if not enabled:
            logger.info("📝 Database service: DISABLED (MVP Mode - Logging only)")
        else:
            logger.info("💾 Database service: ENABLED (Saving to database)")
    
    async def save_detection(
        self,
        camera_id: str,
        image_filename: str,
        plate_data: Dict[str, Any],
        bbox: Optional[list] = None
    ) -> bool:
        """
        บันทึกข้อมูลการตรวจจับรถ
        
        Args:
            camera_id: ID ของกล้อง
            image_filename: ชื่อไฟล์รูปที่บันทึก
            plate_data: ข้อมูลป้ายทะเบียน (จาก AI)
            bbox: ตำแหน่งรถ [x1, y1, x2, y2]
        
        Returns:
            bool: สำเร็จหรือไม่
        """
        try:
            # สร้าง detection record
            detection = {
                "camera_id": camera_id,
                "timestamp": datetime.now().isoformat(),
                "image_path": f"images_logs/{image_filename}",
                "plate_number": plate_data.get("full_plate", "N/A"),
                "province": plate_data.get("province", "N/A"),
                "format_valid": plate_data.get("format_flag", False),
                "bbox": bbox.tolist() if bbox is not None else None,
                "confidence": plate_data.get("confidence", 0.0)
            }
            
            # Phase 1: MVP - Log เป็นไฟล์
            await self._log_to_file(detection)
            
            # Phase 2: บันทึกลง database (ถ้า enabled)
            if self.enabled:
                await self._save_to_database(detection)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save detection: {e}")
            return False
    
    async def _log_to_file(self, detection: Dict[str, Any]):
        """
        Phase 1: บันทึก log ลงไฟล์
        (ใช้งานได้เลยตอนนี้)
        """
        try:
            log_entry = (
                f"[{detection['timestamp']}] "
                f"Camera: {detection['camera_id']} | "
                f"Plate: {detection['plate_number']} | "
                f"Province: {detection['province']} | "
                f"Image: {detection['image_path']}\n"
            )
            
            # Append to log file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            logger.debug(f"Logged detection to file: {detection['plate_number']}")
            
        except Exception as e:
            logger.error(f"Failed to log to file: {e}")
    
    async def _save_to_database(self, detection: Dict[str, Any]):
        """
        Phase 2: บันทึกลงฐานข้อมูล PostgreSQL
        (เปิดใช้งานเมื่อพร้อม)
        
        TODO:
        1. สร้างตาราง detections
        2. เชื่อมต่อ SQLAlchemy
        3. INSERT record
        """
        try:
            # TODO: Implement database save
            # from sqlalchemy.ext.asyncio import AsyncSession
            # async with get_db_session() as session:
            #     db_detection = Detection(**detection)
            #     session.add(db_detection)
            #     await session.commit()
            
            logger.info(f"💾 [TODO] Save to database: {detection['plate_number']}")
            
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        ดูสถิติการตรวจจับ
        """
        try:
            if not os.path.exists(self.log_file):
                return {"total_detections": 0}
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            return {
                "total_detections": len(lines),
                "database_enabled": self.enabled,
                "mode": "Database" if self.enabled else "Log File Only (MVP)"
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}


# ===== Database Models (เตรียมไว้สำหรับ Phase 2) =====

"""
TODO: สร้างตารางเมื่อพร้อมใช้งาน database

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Detection(Base):
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    image_path = Column(String)
    plate_number = Column(String, index=True)
    province = Column(String)
    format_valid = Column(Boolean)
    bbox = Column(JSON)  # [x1, y1, x2, y2]
    confidence = Column(Float)
    
    # Indexes
    __table_args__ = (
        Index('idx_camera_timestamp', 'camera_id', 'timestamp'),
        Index('idx_plate_number', 'plate_number'),
    )
"""
