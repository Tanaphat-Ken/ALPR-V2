import json
import asyncio
from typing import Dict, List, Optional, Callable
from pathlib import Path

from src.models import Camera
from src.services.rtsp_reader import RTSPReader
from src.constants import configs
from src.utils.logging import logger

class CameraManager:
    """
    จัดการกล้องหลายตัว
    - โหลด config จาก JSON
    - เปิด/ปิด stream แต่ละกล้อง
    - จัดการ RTSP readers
    """
    
    def __init__(self):
        self.cameras: Dict[str, Camera] = {}
        self.readers: Dict[str, RTSPReader] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        
    def load_cameras_config(self) -> List[Camera]:
        """โหลด config กล้องจากไฟล์ JSON"""
        try:
            config_path = Path(configs.CAMERAS_CONFIG_PATH)
            
            if not config_path.exists():
                logger.warning(f"Camera config not found: {config_path}")
                return []
            
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cameras = []
            for item in data:
                camera = Camera(
                    id=item['id'],
                    name=item['name'],
                    rtsp_url=item['rtsp_url'],
                    location=item['location'],
                    enabled=item.get('enabled', False),
                    fps=item.get('fps', 10),
                    frame_skip=item.get('frame_skip', 3)
                )
                cameras.append(camera)
                self.cameras[camera.id] = camera
            
            logger.info(f"Loaded {len(cameras)} cameras from config")
            return cameras
            
        except Exception as e:
            logger.error(f"Failed to load cameras config: {e}")
            return []
    
    def get_camera(self, camera_id: str) -> Optional[Camera]:
        """ดึงข้อมูลกล้อง"""
        return self.cameras.get(camera_id)
    
    def get_all_cameras(self) -> List[Camera]:
        """ดึงข้อมูลกล้องทั้งหมด"""
        return list(self.cameras.values())
    
    def get_enabled_cameras(self) -> List[Camera]:
        """ดึงกล้องที่เปิดใช้งาน"""
        return [cam for cam in self.cameras.values() if cam.enabled]
    
    async def start_camera(
        self, 
        camera_id: str, 
        on_frame: Callable,
        on_detection: Callable
    ) -> bool:
        """
        เปิดกล้อง
        
        Args:
            camera_id: ID ของกล้อง
            on_frame: callback เมื่อได้ frame ใหม่
            on_detection: callback เมื่อเจอรถ
        """
        camera = self.get_camera(camera_id)
        
        if camera is None:
            logger.error(f"Camera not found: {camera_id}")
            return False
        
        if camera_id in self.tasks:
            logger.warning(f"Camera already running: {camera_id}")
            return True
        
        try:
            # สร้าง RTSP Reader
            reader = RTSPReader(camera)
            self.readers[camera_id] = reader
            
            # สร้าง task สำหรับ streaming
            task = asyncio.create_task(
                reader.start_streaming(on_frame, on_detection)
            )
            self.tasks[camera_id] = task
            
            logger.info(f"Started camera: {camera.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start camera {camera_id}: {e}")
            return False
    
    async def stop_camera(self, camera_id: str) -> bool:
        """ปิดกล้อง"""
        if camera_id not in self.tasks:
            logger.warning(f"Camera not running: {camera_id}")
            return False
        
        try:
            # หยุด reader
            if camera_id in self.readers:
                self.readers[camera_id].stop()
                del self.readers[camera_id]
            
            # ยกเลิก task
            task = self.tasks[camera_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            del self.tasks[camera_id]
            
            camera = self.get_camera(camera_id)
            logger.info(f"Stopped camera: {camera.name if camera else camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop camera {camera_id}: {e}")
            return False
    
    async def start_all_enabled(self, on_frame: Callable, on_detection: Callable):
        """เปิดกล้องทั้งหมดที่ enabled=true"""
        enabled = self.get_enabled_cameras()
        
        if not enabled:
            logger.warning("No enabled cameras found")
            return
        
        for camera in enabled:
            await self.start_camera(camera.id, on_frame, on_detection)
    
    async def stop_all(self):
        """ปิดกล้องทั้งหมด"""
        camera_ids = list(self.tasks.keys())
        
        for camera_id in camera_ids:
            await self.stop_camera(camera_id)
    
    def get_status(self) -> Dict:
        """ดูสถานะกล้องทั้งหมด"""
        status = {
            "total": len(self.cameras),
            "running": len(self.tasks),
            "cameras": []
        }
        
        for camera in self.cameras.values():
            status["cameras"].append({
                "id": camera.id,
                "name": camera.name,
                "rtsp_url": camera.rtsp_url,
                "location": camera.location,
                "enabled": camera.enabled,
                "fps": camera.fps,
                "frame_skip": camera.frame_skip,
                "running": camera.id in self.tasks
            })
        
        return status
