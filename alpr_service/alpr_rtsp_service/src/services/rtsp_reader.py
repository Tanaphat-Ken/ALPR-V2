import os
import cv2
import asyncio
import numpy as np
from typing import Optional, Callable
from datetime import datetime

from src.models import Camera, VideoPlateTracker
from src.utils.logging import logger

# ไม่ใช้ semaphore fire-and-forget อีกต่อไป
# → ใช้ single detection worker + pending frame buffer
# worker จะเสมอ process frame ล่าสุดที่มีอยู่ ไม่ drop frame ทั้งหมดเมื่อ YOLO ยุ่ง

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
        self.tracker = VideoPlateTracker()  # จะถูก reinit ใน start_streaming ตาม source type
        self._last_good_frame: Optional[np.ndarray] = None

        # --- Single detection worker pattern ---
        # ไม่ใช้ semaphore+fire-and-forget (ทำให้ drop frame ทั้งหมดเมื่อ YOLO ยุ่ง)
        # ใช้ worker + pending buffer: worker เสมอ process frame ล่าสุดที่มีอยู่
        self._pending_frame: Optional[np.ndarray] = None
        self._detection_event: asyncio.Event = asyncio.Event()
        self._detection_worker_task: Optional[asyncio.Task] = None
        
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
        is_file = not self.camera.rtsp_url.startswith('rtsp://')

        if is_file:
            # Video file: imgsz=1280 (accuracy, ไม่ต้อง real-time) — เหมือน websocket service
            self.tracker = VideoPlateTracker(imgsz=1280)
            logger.info(f"[{self.camera.name}] Video file mode: imgsz=1280 (accuracy)")
            await self._stream_video_file(on_frame, on_detection)
        else:
            # RTSP: imgsz=640 (speed, real-time constraint)
            self.tracker = VideoPlateTracker(imgsz=640)
            logger.info(f"[{self.camera.name}] RTSP mode: imgsz=640 (speed)")
            await self._stream_rtsp(on_frame, on_detection)

    async def _stream_video_file(self, on_frame: Callable, on_detection: Callable):
        """
        Video file mode: Sequential detection (ไม่ loop, ไม่ใช้ concurrent worker)
        imgsz=1280 เพื่อ accuracy เท่ากับ websocket service (ไม่ต้อง real-time)
        """
        logger.info(f"[{self.camera.name}] Video file mode: sequential detection (no loop)")

        if not await self.connect():
            logger.error(f"[{self.camera.name}] Failed to open video file")
            self.is_running = False
            return

        try:
            native_fps = self.cap.get(cv2.CAP_PROP_FPS) or self.camera.fps
            frame_delay = 1.0 / native_fps
            consecutive_failures = 0
            max_consecutive_failures = 30

            logger.info(f"[{self.camera.name}] Playing at {native_fps:.1f}fps, frame_skip={self.camera.frame_skip}")

            while self.is_running:
                ret, frame = await self.read_frame()

                if not ret or frame is None:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        logger.info(f"[{self.camera.name}] Video ended (frame {self.frame_count})")
                        # Finalize plate ที่ track ค้างอยู่
                        pending_crop, pending_detected = self.tracker.take_pending_plate()
                        if pending_crop is not None and pending_detected and self._last_good_frame is not None:
                            logger.info(f"[{self.camera.name}] Sending final pending plate")
                            await on_detection(self.camera.id, pending_crop, None, self._last_good_frame)
                        break
                    await asyncio.sleep(0.01)
                    continue

                consecutive_failures = 0
                self._last_good_frame = frame

                if frame.size == 0:
                    continue

                # ✅ Display frame
                try:
                    await on_frame(self.camera.id, frame, self.frame_count)
                except Exception as e:
                    logger.error(f"[{self.camera.name}] Error in on_frame: {e}")

                # ✅ Sequential detection: await YOLO บน frame นี้
                # ถ้ามี GPU: ~30ms → แทบไม่ delay | ถ้า CPU: ~1.5s → slow but correct
                if self.frame_count % self.camera.frame_skip == 0:
                    plate_crop, plate_detected = await self._process_frame(frame)
                    if plate_crop is not None and plate_detected:
                        await on_detection(self.camera.id, plate_crop, None, frame)

                self.frame_count += 1
                # Video file: หน่วง frame_delay เพื่อให้ display ไม่เร็วเกิน
                # (YOLO ใช้เวลาอยู่แล้ว แต่ frame ที่ skip YOLO จะใช้เวลา frame_delay)
                if self.frame_count % self.camera.frame_skip != 0:
                    await asyncio.sleep(frame_delay)

        except Exception as e:
            logger.error(f"[{self.camera.name}] Video streaming error: {e}")
        finally:
            self.disconnect()
            self.is_running = False
            logger.info(f"[{self.camera.name}] Video file playback finished")

    async def _stream_rtsp(self, on_frame: Callable, on_detection: Callable):
        """
        RTSP mode: Concurrent worker (display ที่ native FPS, YOLO ใน background)
        """
        reconnect_delay = 5

        # Start single detection worker
        self._detection_event.clear()
        self._detection_worker_task = asyncio.create_task(
            self._run_detection_worker(on_detection)
        )
        logger.info(f"[{self.camera.name}] RTSP mode: concurrent detection worker started")

        try:
            while self.is_running:
                if not await self.connect():
                    logger.warning(f"[{self.camera.name}] Reconnecting in {reconnect_delay}s...")
                    await asyncio.sleep(reconnect_delay)
                    continue

                self.frame_count = 0
                consecutive_failures = 0
                max_consecutive_failures = 30

                while self.is_running:
                    ret, frame = await self.read_frame()

                    if not ret or frame is None:
                        consecutive_failures += 1
                        if consecutive_failures >= max_consecutive_failures:
                            logger.warning(f"[{self.camera.name}] RTSP stream lost")
                            break
                        await asyncio.sleep(0.01)
                        continue

                    consecutive_failures = 0
                    self._last_good_frame = frame

                    if frame.size == 0:
                        continue

                    try:
                        await on_frame(self.camera.id, frame, self.frame_count)
                    except Exception as e:
                        logger.error(f"[{self.camera.name}] Error in on_frame: {e}")

                    if self.frame_count % self.camera.frame_skip == 0:
                        self._pending_frame = frame.copy()
                        self._detection_event.set()

                    self.frame_count += 1
                    await asyncio.sleep(0.001)

                self.disconnect()
                logger.warning(f"[{self.camera.name}] Reconnecting in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)

        except Exception as e:
            logger.error(f"[{self.camera.name}] RTSP streaming error: {e}")
            self.disconnect()
        finally:
            if self._detection_worker_task and not self._detection_worker_task.done():
                self._detection_event.set()
                self._detection_worker_task.cancel()
                try:
                    await self._detection_worker_task
                except asyncio.CancelledError:
                    pass

    async def _run_detection_worker(self, on_detection: Callable):
        """
        Single detection worker: selects the latest pending frame and runs YOLO.
        Never drops ALL frames - always processes the most recent one available.
        One YOLO at a time → no race condition on shared tracker state.
        """
        logger.info(f"[{self.camera.name}] Detection worker running (imgsz=640, sequential)")
        while self.is_running:
            try:
                # รอจนกว่ามี frame ใหม่มา
                await asyncio.wait_for(self._detection_event.wait(), timeout=1.0)
                self._detection_event.clear()

                # ดึง frame ล่าสุด (อาจถูกแทนที่ระหว่างรอ YOLO)
                frame = self._pending_frame
                if frame is None:
                    continue

                plate_crop, plate_detected = await self._process_frame(frame)
                if plate_crop is not None and plate_detected:
                    await on_detection(self.camera.id, plate_crop, None, frame)

            except asyncio.TimeoutError:
                continue  # timeout ปกติ, loop ต่อ
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.camera.name}] Detection worker error: {e}")
                import traceback
                logger.error(traceback.format_exc())

        logger.info(f"[{self.camera.name}] Detection worker stopped")

    async def _process_frame(self, frame: np.ndarray):
        """ประมวลผล frame ด้วย YOLO tracker (รันใน thread pool เพื่อไม่ block event loop)"""
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