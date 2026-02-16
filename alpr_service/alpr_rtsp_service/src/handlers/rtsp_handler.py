import os
import cv2
import base64
import asyncio
import numpy as np
from io import BytesIO
from typing import Dict, Set, List, Any
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse

from src.services import CameraManager, PlateRecognizerService, DatabaseService
from src.utils.logging import logger
from src.constants import configs

router = APIRouter()

# Global instances
camera_manager = CameraManager()
plate_recognizer = PlateRecognizerService()
database_service = DatabaseService(enabled=configs.DATABASE_ENABLED)

# WebSocket clients สำหรับแต่ละกล้อง
camera_viewers: Dict[str, Set[WebSocket]] = {}

# ✅ เพิ่ม: เก็บ detections ล่าสุดในหน่วยความจำ
recent_detections: Dict[str, List[Dict[str, Any]]] = {}
MAX_RECENT_DETECTIONS = 50


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
        # Encode frame เป็น JPEG - run in thread pool
        loop = asyncio.get_event_loop()
        _, buffer = await loop.run_in_executor(
            None,
            lambda: cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        )
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


async def process_detection(camera_id: str, plate_crop: np.ndarray, bbox, original_frame: np.ndarray):
    """
    ✅ ประมวลผลเมื่อเจอป้ายทะเบียน → ส่ง plate_crop ไป recognizer
    (เหมือน test_rtsp_integration.py - ใช้ /from-plate-crop endpoint)
    """
    try:
        logger.info(f"[{camera_id}] Plate detected, processing...")
        logger.info(f"[{camera_id}] Current viewers: {len(camera_viewers.get(camera_id, set()))}")
        
        # ✅ ส่ง plate_crop (เหมือน test_rtsp_integration.py)
        # Run blocking cv2 operations in thread pool
        loop = asyncio.get_event_loop()
        success, encoded = await loop.run_in_executor(None, cv2.imencode, '.jpg', plate_crop)
        if not success:
            logger.error("Failed to encode plate crop")
            return
        
        from fastapi import UploadFile
        image_stream = BytesIO(encoded.tobytes())
        image_stream.seek(0)
        image_file = UploadFile(
            file=image_stream,
            filename=f"{camera_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
            size=len(encoded.tobytes())
        )
        
        # บันทึกรูป plate crop (local storage) - run in thread pool
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_path = os.path.join(configs.IMAGES_PATH, f"plate_{camera_id}_{timestamp_str}.jpg")
        await loop.run_in_executor(None, cv2.imwrite, save_path, plate_crop)
        logger.info(f"[{camera_id}] Plate crop saved: {save_path}")
        
        # ✅ ส่ง plate_crop ไป AI (เรียก /from-plate-crop endpoint - เหมือน test_rtsp_integration.py)
        try:
            logger.info(f"[{camera_id}] Sending to plate_recognizer (/from-plate-crop)...")
            response = await plate_recognizer.process_plate_crop(image_file)  # ✅ เหมือน test file
            result = response.json()
            
            plate_id = result.get('plate_id', 'N/A')
            province = result.get('province', 'N/A')
            full_plate = result.get('full_plate', 'N/A')
            format_flag = result.get('format_flag', 'unknown')
            
            logger.info(f"[{camera_id}] Recognition result: {full_plate}")
            logger.info(f"[{camera_id}]   - Plate: {plate_id}")
            logger.info(f"[{camera_id}]   - Province: {province}")
            logger.info(f"[{camera_id}]   - Format: {format_flag}")
            
            # ใช้ plate_crop สำหรับแสดงผล (เราส่งรูปนี้ไปแล้ว)
            plate_image_for_display = plate_crop
            plate_bbox = result.get('plate_bbox')
            
            # บันทึกข้อมูลลง database/log
            await database_service.save_detection(
                camera_id=camera_id,
                image_filename=os.path.basename(save_path),
                plate_data=result,
                bbox=plate_bbox
            )
            
            # ✅ เก็บ detection ไว้ใน recent_detections
            # Run blocking cv2 operations in thread pool
            _, buffer = await loop.run_in_executor(
                None, 
                lambda: cv2.imencode('.jpg', plate_image_for_display, [cv2.IMWRITE_JPEG_QUALITY, 90])
            )
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            detection_record = {
                'camera_id': camera_id,
                'timestamp': datetime.now().isoformat(),
                'plate_id': plate_id,
                'province': province,
                'full_plate': full_plate,
                'format_flag': format_flag,
                'image_filename': os.path.basename(save_path),
                'plate_image': f"data:image/jpeg;base64,{image_base64}"
            }
            
            # เก็บไว้ใน memory
            if camera_id not in recent_detections:
                recent_detections[camera_id] = []
            
            recent_detections[camera_id].insert(0, detection_record)
            recent_detections[camera_id] = recent_detections[camera_id][:MAX_RECENT_DETECTIONS]
            
            # ✅ ส่งผลลัพธ์ไปยัง viewers
            logger.info(f"[{camera_id}] Broadcasting detection to viewers...")
            await broadcast_detection(camera_id, result, plate_image_for_display)
            logger.info(f"[{camera_id}] Detection broadcasted successfully")
            
        except Exception as e:
            logger.warning(f"[{camera_id}] AI service error: {e}")
            import traceback
            logger.error(traceback.format_exc()) # ✅ เพิ่ม full traceback
            
            fake_result = {
                "plate_id": "AI Error",
                "province": "N/A",
                "full_plate": "AI Not Available",
                "format_flag": "error"
            }
            
            await database_service.save_detection(
                camera_id=camera_id,
                image_filename=os.path.basename(save_path),
                plate_data=fake_result,
                bbox=None
            )
            
            await broadcast_detection(camera_id, fake_result, plate_crop)
        
    except Exception as e:
        logger.error(f"[{camera_id}] Detection processing error: {e}")
        import traceback
        logger.error(traceback.format_exc()) # ✅ เพิ่ม full traceback


async def broadcast_detection(camera_id: str, result: dict, plate_image: np.ndarray):
    """ส่งผลลัพธ์การอ่านป้ายไปยัง viewers"""
    if camera_id not in camera_viewers or not camera_viewers[camera_id]:
        logger.debug(f"No viewers for camera {camera_id}, skipping broadcast")
        return
    
    try:
        # Encode รูปป้าย - run in thread pool
        loop = asyncio.get_event_loop()
        _, buffer = await loop.run_in_executor(
            None,
            lambda: cv2.imencode('.jpg', plate_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        )
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        result['plate_image'] = f"data:image/jpeg;base64,{image_base64}"
        result['type'] = 'detection'
        result['camera_id'] = camera_id
        result['timestamp'] = datetime.now().isoformat()
        
        # ส่งไปยัง clients
        disconnected = set()
        for websocket in camera_viewers[camera_id]:
            try:
                await websocket.send_json(result)
                logger.info(f"[{camera_id}] Sent detection to viewer")
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
    
    # ✅ เพิ่ม: ส่ง detections ล่าสุด (ถ้ามี) เมื่อ client เชื่อมต่อครั้งแรก
    if camera_id in recent_detections and recent_detections[camera_id]:
        logger.info(f"Sending {len(recent_detections[camera_id])} past detections to new viewer")
        try:
            # ส่ง 5 รายการล่าสุด (จากเก่าไปใหม่)
            for detection in reversed(recent_detections[camera_id][:5]):
                await websocket.send_json({
                    'type': 'detection',
                    'camera_id': detection['camera_id'],
                    'timestamp': detection['timestamp'],
                    'plate_id': detection['plate_id'],
                    'province': detection['province'],
                    'full_plate': detection['full_plate'],
                    'format_flag': detection['format_flag'],
                    'plate_image': detection['plate_image']
                })
                await asyncio.sleep(0.1)  # ให้เวลา client รับข้อมูล
        except Exception as e:
            logger.error(f"Failed to send past detections: {e}")
    
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


@router.get("/cameras/{camera_id}/detections")
async def get_camera_detections(camera_id: str, limit: int = 20):
    """
    ✅ เพิ่ม: ดูรายการ detection ล่าสุดของกล้อง
    """
    camera = camera_manager.get_camera(camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    detections = recent_detections.get(camera_id, [])
    return JSONResponse({
        "camera_id": camera_id,
        "total": len(detections),
        "detections": detections[:limit]
    })


@router.get("/detections/recent")
async def get_all_recent_detections(limit: int = 50):
    """
    ✅ เพิ่ม: ดูรายการ detection ล่าสุดจากทุกกล้อง
    """
    all_detections = []
    
    for camera_id, detections in recent_detections.items():
        all_detections.extend(detections)
    
    # เรียงตาม timestamp (ใหม่สุดก่อน)
    all_detections.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return JSONResponse({
        "total": len(all_detections),
        "detections": all_detections[:limit]
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
    camera_status = camera_manager.get_status()
    db_stats = database_service.get_stats()
    
    return JSONResponse({
        **camera_status,
        "database": db_stats
    })