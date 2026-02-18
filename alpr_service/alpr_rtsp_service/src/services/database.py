"""
Database Service - บันทึกข้อมูลการตรวจจับรถ
รองรับทั้ง file logging และ PostgreSQL database (video_logs table)
"""
import os
import pytz
from datetime import datetime
from typing import Optional, Dict, Any

from src.utils.logging import logger

# เตรียม database connection (optional)
try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.sql import text
    from src.constants import configs
    
    # สร้าง database URL
    DATABASE_URL = f"postgresql+asyncpg://{configs.DB_USER}:{configs.DB_PASSWORD}@{configs.DB_HOST}:{configs.DB_PORT}/{configs.DB_NAME}"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    DB_AVAILABLE = True
except Exception as e:
    logger.warning(f"Database connection not available: {e}")
    DB_AVAILABLE = False
    async_session_factory = None


async def insert_bbox(session, table_name, bbox):
    """
    บันทึก bounding box (4 จุด polygon) ลง database
    
    Args:
        session: SQLAlchemy async session
        table_name: 'car_bbox' หรือ 'plate_bbox'
        bbox: list of 4 points [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    
    Returns:
        bbox_id: ID ของ bbox ที่บันทึก
    """
    query = text(f"""
      INSERT INTO {table_name} (
        top_left_x, top_left_y, 
        top_right_x, top_right_y, 
        bottom_right_x, bottom_right_y,
        bottom_left_x, bottom_left_y
      )
      VALUES (
        :top_left_x, :top_left_y, 
        :top_right_x, :top_right_y, 
        :bottom_right_x, :bottom_right_y,
        :bottom_left_x, :bottom_left_y
      )
      RETURNING {table_name}_id
    """)
    result = await session.execute(query, {
        'top_left_x': bbox[0][0],
        'top_left_y': bbox[0][1],
        'top_right_x': bbox[1][0],
        'top_right_y': bbox[1][1],
        'bottom_right_x': bbox[2][0],
        'bottom_right_y': bbox[2][1],
        'bottom_left_x': bbox[3][0],
        'bottom_left_y': bbox[3][1],
    })
    return result.scalar()


class DatabaseService:
    """
    จัดการการบันทึกข้อมูลลงฐานข้อมูล (video_logs table)
    รองรับทั้ง file logging และ PostgreSQL
    """
    
    def __init__(self, enabled: bool = False):
        """
        Args:
            enabled: เปิด/ปิด การบันทึกลง database
                     False = MVP (แค่ log file)
                     True = บันทึกลง PostgreSQL
        """
        self.enabled = enabled and DB_AVAILABLE
        self.log_file = "images_logs/detections.log"
        
        if not self.enabled:
            logger.info("📝 Database service: DISABLED (MVP Mode - Logging only)")
        else:
            logger.info("💾 Database service: ENABLED (Saving to video_logs)")
    
    async def save_detection(
        self,
        camera_id: str,
        image_filename: str,
        plate_data: Dict[str, Any],
        bbox: Optional[list] = None
    ) -> bool:
        """
        บันทึกข้อมูลการตรวจจับป้ายทะเบียน (เหมือน websocket_video service)
        
        Args:
            camera_id: ID ของกล้อง (แทน token_key)
            image_filename: ชื่อไฟล์รูปที่บันทึก
            plate_data: ข้อมูลป้ายทะเบียน (จาก plate_recognizer)
            bbox: ตำแหน่งป้าย (4 points polygon)
        
        Returns:
            bool: สำเร็จหรือไม่
        """
        try:
            # แปลง bbox ให้เป็น list (รองรับทั้ง numpy array และ list)
            bbox_list = None
            if bbox is not None:
                if hasattr(bbox, 'tolist'):  # numpy array
                    bbox_list = bbox.tolist()
                elif isinstance(bbox, list):  # list อยู่แล้ว
                    bbox_list = bbox
                else:
                    bbox_list = list(bbox)  # อื่นๆ
            
            # สร้าง detection record
            detection = {
                "camera_id": camera_id,
                "timestamp": datetime.now().isoformat(),
                "image_path": f"images_logs/{image_filename}",
                "plate_id": plate_data.get("plate_id", "N/A"),
                "province": plate_data.get("province", "N/A"),
                "full_plate": plate_data.get("full_plate", "N/A"),
                "format_flag": plate_data.get("format_flag", "unknown"),
                "car_bbox": plate_data.get("car_bbox"),
                "plate_bbox": plate_data.get("plate_bbox"),
                "confidence": plate_data.get("confidence", 0.0)
            }
            
            # Phase 1: MVP - Log เป็นไฟล์
            await self._log_to_file(detection)
            
            # Phase 2: บันทึกลง database (ถ้า enabled)
            if self.enabled:
                await self._save_to_video_logs(camera_id, image_filename, plate_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save detection: {e}")
            import traceback
            traceback.print_exc()
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
                f"Plate: {detection['plate_id']} | "  # เปลี่ยนจาก plate_number
                f"Province: {detection['province']} | "
                f"Full: {detection['full_plate']} | "
                f"Flag: {detection['format_flag']} | "
                f"Image: {detection['image_path']}\n"
            )
            
            # Append to log file
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            logger.debug(f"Logged detection to file: {detection['plate_id']}")
            
        except Exception as e:
            logger.error(f"Failed to log to file: {e}")
    
    async def _save_to_video_logs(self, camera_id: str, file_name: str, response: Dict[str, Any]):
        """
        Phase 2: บันทึกลง video_logs table (เหมือน websocket_video service)
        
        Table: video_logs
        Columns: plate_id, file_name, car_bbox_id, plate_bbox_id, 
                 user_id, province, full_plate, format_flag, 
                 token_key, created_at
        
        Note: สำหรับ RTSP service:
              - user_id = NULL (ไม่มี user)
              - token_key = camera_id (แทน token)
        """
        try:
            car_bbox = response.get('car_bbox') if response.get('car_bbox') else None
            plate_bbox = response.get('plate_bbox') if response.get('plate_bbox') else None
            plate_id = response.get('plate_id')
            province = response.get('province')
            full_plate = response.get('full_plate')
            format_flag = response.get('format_flag')

            bkk_time = pytz.timezone('Asia/Bangkok')
            created_at = datetime.now(bkk_time)

            car_bbox_id = None
            plate_bbox_id = None

            async with async_session_factory() as session:
                # บันทึก bboxes (ถ้ามี)
                if car_bbox:
                    car_bbox_id = await insert_bbox(session, 'car_bbox', car_bbox)
                if plate_bbox:
                    plate_bbox_id = await insert_bbox(session, 'plate_bbox', plate_bbox)

                # บันทึกลง video_logs
                query = text("""
                    INSERT INTO video_logs (
                        plate_id, file_name, car_bbox_id, plate_bbox_id, 
                        user_id, province, full_plate, format_flag, 
                        token_key, created_at
                    )
                    VALUES (
                        :plate_id, :file_name, :car_bbox_id, :plate_bbox_id, 
                        :user_id, :province, :full_plate, :format_flag, 
                        :token_key, :created_at
                    )
                """)
                await session.execute(query, {
                    'plate_id': plate_id,
                    'file_name': file_name,
                    'car_bbox_id': car_bbox_id,
                    'plate_bbox_id': plate_bbox_id,
                    'user_id': None,  # RTSP service ไม่มี user
                    'province': province,
                    'full_plate': full_plate,
                    'format_flag': format_flag,
                    'token_key': camera_id,  # ใช้ camera_id แทน token
                    'created_at': created_at.replace(tzinfo=None)
                })

                await session.commit()
                logger.info(f"💾 Saved to video_logs: {full_plate} (camera: {camera_id})")

        except Exception as e:
            logger.error(f"Failed to save to video_logs: {e}")
            if 'session' in locals():
                await session.rollback()
    
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
