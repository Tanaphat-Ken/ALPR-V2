import os
import cv2
import base64
import asyncio
import numpy as np
from io import BytesIO
from typing import Dict, Set, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.services import (
    CameraManager, PlateRecognizerService, DatabaseService,
    db_get_all_streams, db_get_stream, db_create_stream,
    db_update_stream, db_delete_stream, db_save_detection,
    db_validate_rtsp_token, db_get_user_id_from_token, DB_AVAILABLE,
)
from src.models import Camera
from src.utils.logging import logger
from src.constants import configs

router = APIRouter()

# Global instances
camera_manager = CameraManager()
plate_recognizer = PlateRecognizerService()
database_service = DatabaseService(enabled=configs.DATABASE_ENABLED)

# map stream_id (int) → camera string id
# ใช้สำหรับส่ง stream_id ตอน save detection log
_stream_id_map: Dict[str, Optional[int]] = {}  # camera_id → stream_id

# Deduplication: ป้องกัน save ป้ายเดิมซ้ำเมื่อ video loop
# key = (camera_id, plate_text)  value = timestamp ของการ detect ครั้งล่าสุด
_last_detected: Dict[tuple, datetime] = {}
PLATE_COOLDOWN_SECONDS = 3  # เหมือน websocket service: ป้ายเดิมใน 3 วินาที → skip


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class StreamCreate(BaseModel):
    name: str
    rtsp_url: str
    token_key: str  # จำเป็น — token ประเภท RTSP ของ user
    location: Optional[str] = None
    enabled: bool = False
    fps: int = 10
    frame_skip: int = 3

class StreamUpdate(BaseModel):
    name: Optional[str] = None
    rtsp_url: Optional[str] = None
    token_key: Optional[str] = None
    location: Optional[str] = None
    enabled: Optional[bool] = None
    fps: Optional[int] = None
    frame_skip: Optional[int] = None

# WebSocket clients สำหรับแต่ละกล้อง
camera_viewers: Dict[str, Set[WebSocket]] = {}

# ✅ เพิ่ม: เก็บ detections ล่าสุดในหน่วยความจำ
recent_detections: Dict[str, List[Dict[str, Any]]] = {}
MAX_RECENT_DETECTIONS = 50


async def startup_rtsp():
    """โหลด config จาก DB ก่อน แล้ว fallback ไป cameras.json"""
    logger.info("Starting RTSP service...")

    loaded_from_db = False
    if DB_AVAILABLE:
        try:
            rows = await db_get_all_streams()
            if rows:
                for row in rows:
                    cam_id = str(row["stream_id"])
                    camera = Camera(
                        id=cam_id,
                        name=row["name"],
                        rtsp_url=row["rtsp_url"],
                        location=row.get("location") or "",
                        enabled=row["enabled"],
                        fps=row.get("fps", 10),
                        frame_skip=row.get("frame_skip", 3),
                        token_key=row.get("token_key"),
                    )
                    camera_manager.cameras[cam_id] = camera
                    _stream_id_map[cam_id] = row["stream_id"]
                logger.info(f"Loaded {len(rows)} cameras from database")
                loaded_from_db = True
        except Exception as e:
            logger.warning(f"Could not load cameras from DB: {e}")

    if not loaded_from_db:
        logger.info("Falling back to cameras.json config")
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
        loop = asyncio.get_running_loop()
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
        loop = asyncio.get_running_loop()
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

            # ✅ Deduplication: skip ถ้าป้ายเดิมถูก detect ภายใน cooldown window
            dedup_key = (camera_id, full_plate)
            now = datetime.now()
            last_time = _last_detected.get(dedup_key)
            if last_time is not None:
                elapsed = (now - last_time).total_seconds()
                if elapsed < PLATE_COOLDOWN_SECONDS:
                    logger.info(f"[{camera_id}] Duplicate plate '{full_plate}' (last seen {elapsed:.0f}s ago, cooldown={PLATE_COOLDOWN_SECONDS}s) — skipping save")
                    return
            _last_detected[dedup_key] = now
            
            # ใช้ plate_crop สำหรับแสดงผล (เราส่งรูปนี้ไปแล้ว)
            plate_image_for_display = plate_crop
            plate_bbox = result.get('plate_bbox')
            
            # บันทึกข้อมูลลง database/log
            stream_id = _stream_id_map.get(camera_id)
            if DB_AVAILABLE:
                await db_save_detection(
                    camera_id=camera_id,
                    file_name=os.path.basename(save_path),
                    plate_data=result,
                    stream_id=stream_id,
                )
            else:
                await database_service.save_detection(
                    camera_id=camera_id,
                    image_filename=os.path.basename(save_path),
                    plate_data=result,
                    bbox=plate_bbox,
                )
            
            # ✅ เก็บ detection ไว้ใน recent_detections
            # Run blocking cv2 operations in thread pool
            
            # Encode plate crop image
            _, buffer = await loop.run_in_executor(
                None, 
                lambda: cv2.imencode('.jpg', plate_image_for_display, [cv2.IMWRITE_JPEG_QUALITY, 90])
            )
            plate_image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Resize and encode full frame (เหมือนเพื่อนทำ - resize เป็น 480px width)
            def resize_and_encode_frame(frame):
                height, width = frame.shape[:2]
                target_width = 480
                aspect_ratio = height / width
                target_height = int(target_width * aspect_ratio)
                resized = cv2.resize(frame, (target_width, target_height))
                _, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
                return base64.b64encode(buffer).decode('utf-8')
            
            full_image_base64 = await loop.run_in_executor(None, resize_and_encode_frame, original_frame)
            
            detection_record = {
                'camera_id': camera_id,
                'timestamp': datetime.now().isoformat(),
                'plate_id': plate_id,
                'province': province,
                'full_plate': full_plate,
                'format_flag': format_flag,
                'image_filename': os.path.basename(save_path),
                'plate_image': f"data:image/jpeg;base64,{plate_image_base64}",
                'full_image': f"data:image/jpeg;base64,{full_image_base64}"
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
            
            stream_id = _stream_id_map.get(camera_id)
            if DB_AVAILABLE:
                await db_save_detection(
                    camera_id=camera_id,
                    file_name=os.path.basename(save_path),
                    plate_data=fake_result,
                    stream_id=stream_id,
                )
            else:
                await database_service.save_detection(
                    camera_id=camera_id,
                    image_filename=os.path.basename(save_path),
                    plate_data=fake_result,
                    bbox=None,
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
        loop = asyncio.get_running_loop()
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
    """ดูรายการกล้องทั้งหมด (รวม stream_id สำหรับ CRUD)"""
    status = camera_manager.get_status()
    # แนบ stream_id กลับไปด้วย
    for cam in status["cameras"]:
        cam["stream_id"] = _stream_id_map.get(cam["id"])
    return JSONResponse(status)


# ---------------------------------------------------------------------------
# CRUD Endpoints
# ---------------------------------------------------------------------------

@router.post("/cameras")
async def create_camera(body: StreamCreate):
    """สร้างกล้องใหม่ (บันทึกลง DB) — ต้องใช้ RTSP token ที่ถูกต้อง"""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")

    # ตรวจสอบ token
    token_info = await db_validate_rtsp_token(body.token_key)
    if not token_info:
        raise HTTPException(
            status_code=403,
            detail="Invalid RTSP token: token not found, expired, or subscription does not include RTSP access"
        )

    user_id = token_info["user_id"]
    data = body.model_dump(exclude={"token_key"})
    row = await db_create_stream(data, user_id=user_id, token_key=body.token_key)
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create stream")

    cam_id = str(row["stream_id"])
    camera = Camera(
        id=cam_id,
        name=row["name"],
        rtsp_url=row["rtsp_url"],
        location=row.get("location") or "",
        enabled=row["enabled"],
        fps=row.get("fps", 10),
        frame_skip=row.get("frame_skip", 3),
        token_key=body.token_key,
    )
    camera_manager.cameras[cam_id] = camera
    _stream_id_map[cam_id] = row["stream_id"]

    # เริ่ม stream ทันทีถ้า enabled
    if camera.enabled:
        await camera_manager.start_camera(cam_id, on_frame=broadcast_frame, on_detection=process_detection)

    return JSONResponse({**row, "id": cam_id, "running": cam_id in camera_manager.tasks}, status_code=201)


@router.put("/cameras/{camera_id}")
async def update_camera(camera_id: str, body: StreamUpdate):
    """แก้ไขข้อมูลกล้อง"""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")

    stream_id = _stream_id_map.get(camera_id)
    if stream_id is None:
        raise HTTPException(status_code=404, detail="Camera not found")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}

    # ถ้ามีการเปลี่ยน token_key ตรวจสอบ validity
    if "token_key" in updates:
        token_info = await db_validate_rtsp_token(updates["token_key"])
        if not token_info:
            raise HTTPException(
                status_code=403,
                detail="Invalid RTSP token: token not found, expired, or subscription does not include RTSP access"
            )

    row = await db_update_stream(stream_id, updates)
    if not row:
        raise HTTPException(status_code=500, detail="Failed to update stream")

    # อัปเดต in-memory camera
    cam = camera_manager.cameras.get(camera_id)
    if cam:
        for k, v in updates.items():
            if hasattr(cam, k):
                setattr(cam, k, v)

    # ถ้า enabled เปลี่ยน → start/stop
    if "enabled" in updates:
        if updates["enabled"] and camera_id not in camera_manager.tasks:
            await camera_manager.start_camera(camera_id, on_frame=broadcast_frame, on_detection=process_detection)
        elif not updates["enabled"] and camera_id in camera_manager.tasks:
            await camera_manager.stop_camera(camera_id)

    def serialize(v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v
    return JSONResponse({**{k: serialize(v) for k, v in row.items()}, "id": camera_id, "running": camera_id in camera_manager.tasks})


@router.delete("/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    """ลบกล้อง"""
    stream_id = _stream_id_map.get(camera_id)

    # หยุด stream ก่อน
    if camera_id in camera_manager.tasks:
        await camera_manager.stop_camera(camera_id)

    # ลบจาก in-memory
    camera_manager.cameras.pop(camera_id, None)
    _stream_id_map.pop(camera_id, None)

    # ลบจาก DB (ถ้ามี)
    if DB_AVAILABLE and stream_id is not None:
        await db_delete_stream(stream_id)

    return JSONResponse({"message": "Camera deleted", "camera_id": camera_id})


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