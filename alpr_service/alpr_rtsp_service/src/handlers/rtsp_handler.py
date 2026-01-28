import os
import cv2
import base64
import asyncio
import numpy as np
from io import BytesIO
from typing import Dict, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse

from src.services import CameraManager, PlateRecognizerService
from src.utils.logging import logger
from src.constants import configs

router = APIRouter()

# Global instances
camera_manager = CameraManager()
plate_recognizer = PlateRecognizerService()

# WebSocket clients สำหรับแต่ละกล้อง
camera_viewers: Dict[str, Set[WebSocket]] = {}


async def startup_rtsp():
    """โหลด config และเริ่มกล้องที่เปิดใช้งาน"""
    logger.info("Starting RTSP service...")
    camera_manager.load_cameras_config()
    
    # เริ่มกล้องที่ enabled=true
    await camera_manager.start_all_enabled(
        on_frame=broadcast_frame,
        on_detection=process_detection
    )


async def shutdown_rtsp():
    """ปิดกล้องทั้งหมด"""
    logger.info("Shutting down RTSP service...")
    await camera_manager.stop_all()


async def broadcast_frame(camera_id: str, frame: np.ndarray, frame_count: int):
    """
    ส่ง frame ไปยัง WebSocket clients ทั้งหมดที่ดูกล้องนี้
    (สำหรับแสดงผลบนหน้าเว็บ)
    """
    if camera_id not in camera_viewers or not camera_viewers[camera_id]:
        return
    
    try:
        # Encode frame เป็น JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # ส่งไปยัง clients
        disconnected = set()
        for websocket in camera_viewers[camera_id]:
            try:
                await websocket.send_json({
                    "type": "frame",
                    "camera_id": camera_id,
                    "frame_count": frame_count,
                    "image": f"data:image/jpeg;base64,{frame_base64}"
                })
            except Exception as e:
                disconnected.add(websocket)
        
        # ลบ clients ที่ตัดการเชื่อมต่อ
        camera_viewers[camera_id] -= disconnected
        
    except Exception as e:
        logger.error(f"Error broadcasting frame: {e}")


async def process_detection(camera_id: str, car_image: np.ndarray, bbox, original_frame: np.ndarray):
    """
    ประมวลผลเมื่อเจอรถ → ส่งไปอ่านป้ายทะเบียน
    """
    try:
        logger.info(f"[{camera_id}] Car detected, processing...")
        
        # แปลง numpy array เป็น UploadFile
        success, encoded = cv2.imencode('.jpg', car_image)
        if not success:
            logger.error("Failed to encode car image")
            return
        
        from fastapi import UploadFile
        image_stream = BytesIO(encoded.tobytes())
        image_file = UploadFile(
            file=image_stream,
            filename=f"{camera_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        )
        
        # บันทึกรูป (optional)
        save_path = os.path.join(configs.IMAGES_PATH, image_file.filename)
        cv2.imwrite(save_path, car_image)
        logger.info(f"[{camera_id}] Car image saved: {save_path}")
        
        # ลองส่งไป AI (ถ้าไม่ได้ก็ข้าม)
        try:
            response = await plate_recognizer.process_image(bbox, image_file)
            result = response.json()
            logger.info(f"[{camera_id}] Plate: {result.get('full_plate', 'N/A')}")
            
            # ส่งผลลัพธ์ไปยัง viewers
            await broadcast_detection(camera_id, result, car_image)
        except Exception as e:
            logger.warning(f"[{camera_id}] AI service not available: {e}")
            # ส่งแค่รูปรถโดยไม่มีข้อมูลป้าย
            fake_result = {
                "full_plate": "AI Not Available",
                "province": "N/A",
                "format_flag": False
            }
            await broadcast_detection(camera_id, fake_result, car_image)
        
    except Exception as e:
        logger.error(f"[{camera_id}] Detection processing error: {e}")


async def broadcast_detection(camera_id: str, result: dict, car_image: np.ndarray):
    """ส่งผลลัพธ์การอ่านป้ายไปยัง viewers"""
    if camera_id not in camera_viewers or not camera_viewers[camera_id]:
        return
    
    try:
        # Encode รูปรถ
        _, buffer = cv2.imencode('.jpg', car_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        result['car_image'] = f"data:image/jpeg;base64,{image_base64}"
        result['type'] = 'detection'
        result['camera_id'] = camera_id
        result['timestamp'] = datetime.now().isoformat()
        
        # ส่งไปยัง clients
        disconnected = set()
        for websocket in camera_viewers[camera_id]:
            try:
                await websocket.send_json(result)
            except Exception:
                disconnected.add(websocket)
        
        camera_viewers[camera_id] -= disconnected
        
    except Exception as e:
        logger.error(f"Error broadcasting detection: {e}")


@router.websocket("/stream/{camera_id}")
async def stream_websocket(websocket: WebSocket, camera_id: str):
    """
    WebSocket endpoint สำหรับดู stream จากกล้อง
    """
    await websocket.accept()
    
    camera = camera_manager.get_camera(camera_id)
    if camera is None:
        await websocket.send_json({"error": "Camera not found"})
        await websocket.close()
        return
    
    # เพิ่ม client เข้า viewers
    if camera_id not in camera_viewers:
        camera_viewers[camera_id] = set()
    camera_viewers[camera_id].add(websocket)
    
    logger.info(f"Client connected to camera: {camera.name}")
    
    # ส่งข้อมูลกล้อง
    await websocket.send_json({
        "type": "info",
        "camera": {
            "id": camera.id,
            "name": camera.name,
            "location": camera.location
        }
    })
    
    try:
        # รอให้ client ตัดการเชื่อมต่อ
        while True:
            data = await websocket.receive_text()
            # สามารถรับคำสั่งจาก client ได้ที่นี่
            
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from camera: {camera.name}")
    finally:
        if camera_id in camera_viewers:
            camera_viewers[camera_id].discard(websocket)


@router.get("/cameras")
async def get_cameras():
    """ดูรายการกล้องทั้งหมด"""
    return JSONResponse(camera_manager.get_status())


@router.get("/cameras/{camera_id}")
async def get_camera(camera_id: str):
    """ดูข้อมูลกล้อง"""
    camera = camera_manager.get_camera(camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    return JSONResponse({
        "id": camera.id,
        "name": camera.name,
        "location": camera.location,
        "enabled": camera.enabled,
        "running": camera_id in camera_manager.tasks
    })


@router.post("/cameras/{camera_id}/start")
async def start_camera(camera_id: str):
    """เปิดกล้อง"""
    success = await camera_manager.start_camera(
        camera_id,
        on_frame=broadcast_frame,
        on_detection=process_detection
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start camera")
    
    return JSONResponse({"message": "Camera started", "camera_id": camera_id})


@router.post("/cameras/{camera_id}/stop")
async def stop_camera(camera_id: str):
    """ปิดกล้อง"""
    success = await camera_manager.stop_camera(camera_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to stop camera")
    
    return JSONResponse({"message": "Camera stopped", "camera_id": camera_id})


@router.get("/status")
async def get_status():
    """ดูสถานะระบบ"""
    return JSONResponse(camera_manager.get_status())
