import os
import cv2
import asyncio
import numpy as np
from typing import Optional, Callable
from datetime import datetime

from src.models import Camera, VideoPlateTracker
from src.utils.logging import logger

class RTSPReader:
    """
    อ่าน RTSP stream จากกล้อง IP Camera
    รองรับทั้ง RTSP URL และไฟล์วิดีโอ (สำหรับทดสอบ)
    ใช้ VideoPlateTracker เพื่อ detect ป้ายทะเบียนโดยตรง
    """
    
    def __init__(self, camera: Camera):
        self.camera = camera
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.frame_count = 0
        self.tracker = VideoPlateTracker()  # ✅ เปลี่ยนเป็น VideoPlateTracker
        
    async def connect(self) -> bool:
        """เชื่อมต่อกับกล้อง"""
        try:
            logger.info(f"[{self.camera.name}] Connecting to {self.camera.rtsp_url}")
            
            # รัน cv2.VideoCapture ใน thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            self.cap = await loop.run_in_executor(
                None, cv2.VideoCapture, self.camera.rtsp_url
            )
            
            if not self.cap.isOpened():
                logger.error(f"[{self.camera.name}] Failed to open stream")
                return False
            
            logger.info(f"[{self.camera.name}] Connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"[{self.camera.name}] Connection error: {e}")
            return False
    
    async def read_frame(self) -> tuple[bool, Optional[np.ndarray]]:
        """อ่าน frame เดียว"""
        if self.cap is None or not self.cap.isOpened():
            return False, None
        
        try:
            loop = asyncio.get_event_loop()
            ret, frame = await loop.run_in_executor(None, self.cap.read)
            return ret, frame
        except Exception as e:
            logger.error(f"[{self.camera.name}] Read frame error: {e}")
            return False, None
    
    async def start_streaming(self, on_frame: Callable, on_detection: Callable):
        """
        เริ่ม streaming และประมวลผล
        
        Args:
            on_frame: callback สำหรับส่ง frame ทุกๆ frame (สำหรับแสดงผล)
            on_detection: callback เมื่อเจอป้ายทะเบียน (สำหรับอ่านป้าย)
        """
        self.is_running = True
        reconnect_delay = 5
        
        while self.is_running:
            try:
                # เชื่อมต่อกล้อง
                if not await self.connect():
                    logger.warning(f"[{self.camera.name}] Reconnecting in {reconnect_delay}s...")
                    await asyncio.sleep(reconnect_delay)
                    continue
                
                self.frame_count = 0
                consecutive_failures = 0
                max_consecutive_failures = 30  # ถ้าอ่านไม่ได้ 30 frame ติดกัน ถึงจะถือว่าจบ
                
                # อ่าน frames ต่อเนื่อง
                while self.is_running:
                    ret, frame = await self.read_frame()
                    
                    if not ret or frame is None:
                        consecutive_failures += 1
                        logger.debug(f"[{self.camera.name}] Failed to read frame ({consecutive_failures}/{max_consecutive_failures})")
                        
                        # ถ้าอ่านไม่ได้หลายครั้งติดกัน → ถือว่าจบจริงๆ
                        if consecutive_failures >= max_consecutive_failures:
                            logger.warning(f"[{self.camera.name}] End of video/stream (consecutive failures: {consecutive_failures})")
                            # ถ้าเป็นไฟล์วิดีโอ → loop กลับไปเริ่มต้น
                            if not self.camera.rtsp_url.startswith('rtsp://'):
                                logger.info(f"[{self.camera.name}] Looping video...")
                                self.disconnect()
                                await asyncio.sleep(1)
                                break  # reconnect
                            else:
                                break  # RTSP ขาดการเชื่อมต่อจริงๆ
                        
                        # ข้าม frame ที่เสีย แล้วลองต่อ
                        await asyncio.sleep(0.01)
                        continue
                    
                    # อ่านสำเร็จ → reset counter
                    consecutive_failures = 0
                    
                    # ตรวจสอบ corrupted frame (HEVC decoder error)
                    if frame.size == 0:
                        logger.debug(f"[{self.camera.name}] Corrupted frame (size=0), skipping...")
                        continue
                    
                    # ✅ ส่ง frame ไปแสดงผล (wrap ด้วย try-except เพื่อไม่ให้ error ทำให้หยุด)
                    try:
                        await on_frame(self.camera.id, frame, self.frame_count)
                    except Exception as e:
                        logger.error(f"[{self.camera.name}] Error in on_frame callback: {e}")
                        # ไม่ break, ทำงานต่อไป
                    
                    # ประมวลผลเฉพาะบาง frames (เพื่อประหยัด CPU)
                    if self.frame_count % self.camera.frame_skip == 0:
                        try:
                            plate_crop, plate_detected = await self._process_frame(frame)
                            
                            if plate_crop is not None and plate_detected:
                                # ✅ wrap callback ด้วย try-except เพื่อไม่ให้ error ทำให้ stream หยุด
                                try:
                                    await on_detection(self.camera.id, plate_crop, None, frame)
                                except Exception as e:
                                    logger.error(f"[{self.camera.name}] Error in on_detection callback: {e}")
                                    import traceback
                                    logger.error(traceback.format_exc())
                                    # ไม่ break loop, ทำงานต่อไป
                        except Exception as e:
                            logger.error(f"[{self.camera.name}] Error in detection processing: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            # ไม่ break loop, ทำงานต่อไป
                    
                    self.frame_count += 1
                    
                    # จำกัด FPS
                    await asyncio.sleep(1.0 / self.camera.fps)
                
                # ขาดการเชื่อมต่อ
                self.disconnect()
                logger.warning(f"[{self.camera.name}] Reconnecting in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)
                
            except Exception as e:
                logger.error(f"[{self.camera.name}] Streaming error: {e}")
                self.disconnect()
                await asyncio.sleep(reconnect_delay)
    
    async def _process_frame(self, frame: np.ndarray):
        """ประมวลผล frame ด้วย YOLO tracker"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.tracker.process_frame, frame)
    
    def stop(self):
        """หยุดการทำงาน"""
        logger.info(f"[{self.camera.name}] Stopping...")
        self.is_running = False
        self.disconnect()
    
    def disconnect(self):
        """ตัดการเชื่อมต่อ"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            logger.info(f"[{self.camera.name}] Disconnected")