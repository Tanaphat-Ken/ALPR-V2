"""
Stream Database Service
- CRUD สำหรับ rtsp_streams table
- บันทึก detection logs ลง video_logs (พร้อม stream_id + service_type)
"""
import os
import pytz
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.utils.logging import logger
from src.constants import configs

try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.sql import text

    DATABASE_URL = (
        f"postgresql+asyncpg://{configs.DB_USER}:{configs.DB_PASSWORD}"
        f"@{configs.DB_HOST}:{configs.DB_PORT}/{configs.DB_NAME}"
    )
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_factory = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    DB_AVAILABLE = True
except Exception as e:
    logger.warning(f"Database connection not available: {e}")
    DB_AVAILABLE = False
    async_session_factory = None


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _insert_bbox(session: "AsyncSession", table_name: str, bbox: list) -> Optional[int]:
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
        "top_left_x":     bbox[0][0], "top_left_y":     bbox[0][1],
        "top_right_x":    bbox[1][0], "top_right_y":    bbox[1][1],
        "bottom_right_x": bbox[2][0], "bottom_right_y": bbox[2][1],
        "bottom_left_x":  bbox[3][0], "bottom_left_y":  bbox[3][1],
    })
    return result.scalar()


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

async def db_validate_rtsp_token(token_key: str) -> Optional[Dict]:
    """
    ตรวจสอบว่า token_key:
      1. มีอยู่ใน DB
      2. service_type = 'RTSP'
      3. ยังไม่หมดอายุ (expire_time IS NULL หรือ > NOW())
      4. subscription มี has_rtsp_stream = 1
    คืนค่า dict(token_key, user_id, user_sub_id) หรือ None ถ้าไม่ผ่าน
    """
    if not DB_AVAILABLE:
        return None
    try:
        async with async_session_factory() as session:
            q = text("""
                SELECT t.key AS token_key,
                       us.user_id,
                       t.user_sub_id,
                       t.expire_time,
                       s.has_rtsp_stream
                FROM token t
                JOIN user_subscription us ON t.user_sub_id = us.user_sub_id
                JOIN subscription s ON us.sub_id = s.sub_id
                WHERE t.key = :token_key
                  AND t.service_type = 'RTSP'
                  AND (t.expire_time IS NULL OR t.expire_time > NOW())
                  AND s.has_rtsp_stream = 1
                  AND us.is_activate = TRUE
                LIMIT 1
            """)
            result = await session.execute(q, {"token_key": token_key})
            row = result.mappings().first()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"db_validate_rtsp_token error: {e}")
        return None


async def db_get_user_id_from_token(token_key: str) -> Optional[int]:
    """แปลง token_key → user_id (ผ่าน user_subscription)"""
    if not DB_AVAILABLE:
        return None
    try:
        async with async_session_factory() as session:
            q = text("""
                SELECT us.user_id
                FROM token t
                JOIN user_subscription us ON t.user_sub_id = us.user_sub_id
                WHERE t.key = :token_key
                LIMIT 1
            """)
            result = await session.execute(q, {"token_key": token_key})
            row = result.mappings().first()
            return row["user_id"] if row else None
    except Exception as e:
        logger.error(f"db_get_user_id_from_token error: {e}")
        return None


# ---------------------------------------------------------------------------
# Stream CRUD
# ---------------------------------------------------------------------------

async def db_get_all_streams(user_id: Optional[int] = None) -> List[Dict]:
    """ดึง streams ทั้งหมด (หรือเฉพาะ user)"""
    if not DB_AVAILABLE:
        return []
    try:
        async with async_session_factory() as session:
            if user_id is not None:
                q = text("""
                    SELECT stream_id, name, rtsp_url, location, enabled, fps, frame_skip,
                           user_id, token_key, created_at, updated_at
                    FROM rtsp_streams WHERE user_id = :user_id
                    ORDER BY created_at DESC
                """)
                result = await session.execute(q, {"user_id": user_id})
            else:
                q = text("""
                    SELECT stream_id, name, rtsp_url, location, enabled, fps, frame_skip,
                           user_id, token_key, created_at, updated_at
                    FROM rtsp_streams
                    ORDER BY created_at DESC
                """)
                result = await session.execute(q)
            rows = result.mappings().all()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"db_get_all_streams error: {e}")
        return []


async def db_get_stream(stream_id: int) -> Optional[Dict]:
    if not DB_AVAILABLE:
        return None
    try:
        async with async_session_factory() as session:
            q = text("""
                SELECT stream_id, name, rtsp_url, location, enabled, fps, frame_skip,
                       user_id, token_key, created_at, updated_at
                FROM rtsp_streams WHERE stream_id = :id
            """)
            result = await session.execute(q, {"id": stream_id})
            row = result.mappings().first()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"db_get_stream error: {e}")
        return None


async def db_create_stream(data: Dict, user_id: Optional[int] = None, token_key: Optional[str] = None) -> Optional[Dict]:
    if not DB_AVAILABLE:
        return None
    try:
        async with async_session_factory() as session:
            q = text("""
                INSERT INTO rtsp_streams (name, rtsp_url, location, enabled, fps, frame_skip, user_id, token_key, created_at, updated_at)
                VALUES (:name, :rtsp_url, :location, :enabled, :fps, :frame_skip, :user_id, :token_key, NOW(), NOW())
                RETURNING stream_id, name, rtsp_url, location, enabled, fps, frame_skip, user_id, token_key, created_at, updated_at
            """)
            result = await session.execute(q, {
                "name":       data["name"],
                "rtsp_url":   data["rtsp_url"],
                "location":   data.get("location"),
                "enabled":    data.get("enabled", False),
                "fps":        data.get("fps", 10),
                "frame_skip": data.get("frame_skip", 3),
                "user_id":    user_id,
                "token_key":  token_key,
            })
            await session.commit()
            row = result.mappings().first()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"db_create_stream error: {e}")
        return None


async def db_update_stream(stream_id: int, data: Dict) -> Optional[Dict]:
    if not DB_AVAILABLE:
        return None
    try:
        async with async_session_factory() as session:
            # build SET clause dynamically from provided fields
            allowed = {"name", "rtsp_url", "location", "enabled", "fps", "frame_skip", "token_key"}
            updates = {k: v for k, v in data.items() if k in allowed}
            if not updates:
                return await db_get_stream(stream_id)

            set_clause = ", ".join(f"{k} = :{k}" for k in updates)
            updates["stream_id"] = stream_id
            q = text(f"""
                UPDATE rtsp_streams
                SET {set_clause}, updated_at = NOW()
                WHERE stream_id = :stream_id
                RETURNING stream_id, name, rtsp_url, location, enabled, fps, frame_skip,
                          user_id, token_key, created_at, updated_at
            """)
            result = await session.execute(q, updates)
            await session.commit()
            row = result.mappings().first()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"db_update_stream error: {e}")
        return None


async def db_delete_stream(stream_id: int) -> bool:
    if not DB_AVAILABLE:
        return False
    try:
        async with async_session_factory() as session:
            q = text("DELETE FROM rtsp_streams WHERE stream_id = :id")
            await session.execute(q, {"id": stream_id})
            await session.commit()
            return True
    except Exception as e:
        logger.error(f"db_delete_stream error: {e}")
        return False


# ---------------------------------------------------------------------------
# Detection logging
# ---------------------------------------------------------------------------

async def db_save_detection(
    camera_id: str,
    file_name: str,
    plate_data: Dict[str, Any],
    stream_id: Optional[int] = None,
) -> bool:
    """
    บันทึกผล detection ลง video_logs
    - token_key  = camera_id (string)
    - service_type = 'RTSP'
    - stream_id  = FK กลับ rtsp_streams (ถ้ามี)
    - user_id    = ดึงจาก rtsp_streams (ถ้ามี)
    """
    if not DB_AVAILABLE:
        return False
    try:
        car_bbox  = plate_data.get("car_bbox")
        plate_bbox = plate_data.get("plate_bbox")
        plate_id   = plate_data.get("plate_id")
        province   = plate_data.get("province")
        full_plate = plate_data.get("full_plate")
        format_flag = plate_data.get("format_flag")

        bkk_tz = pytz.timezone("Asia/Bangkok")
        created_at = datetime.now(bkk_tz).replace(tzinfo=None)

        # resolve user_id and token_key จาก stream_id (ถ้ามี)
        user_id = None
        real_token_key = camera_id  # fallback
        if stream_id is not None:
            row = await db_get_stream(stream_id)
            if row:
                user_id = row.get("user_id")
                real_token_key = row.get("token_key") or camera_id

        car_bbox_id = plate_bbox_id = None

        async with async_session_factory() as session:
            if car_bbox:
                bbox = car_bbox.tolist() if hasattr(car_bbox, "tolist") else car_bbox
                car_bbox_id = await _insert_bbox(session, "car_bbox", bbox)
            if plate_bbox:
                bbox = plate_bbox.tolist() if hasattr(plate_bbox, "tolist") else plate_bbox
                plate_bbox_id = await _insert_bbox(session, "plate_bbox", bbox)

            q = text("""
                INSERT INTO video_logs (
                    plate_id, file_name, car_bbox_id, plate_bbox_id,
                    user_id, province, full_plate, format_flag,
                    token_key, created_at, service_type, stream_id
                )
                VALUES (
                    :plate_id, :file_name, :car_bbox_id, :plate_bbox_id,
                    :user_id, :province, :full_plate, :format_flag,
                    :token_key, :created_at, :service_type, :stream_id
                )
            """)
            await session.execute(q, {
                "plate_id":    plate_id,
                "file_name":   file_name,
                "car_bbox_id": car_bbox_id,
                "plate_bbox_id": plate_bbox_id,
                "user_id":     user_id,
                "province":    province,
                "full_plate":  full_plate,
                "format_flag": format_flag,
                "token_key":   real_token_key,
                "created_at":  created_at,
                "service_type": "RTSP",
                "stream_id":   stream_id,
            })
            await session.commit()
            logger.info(f"💾 video_logs saved: {full_plate} (camera={camera_id})")
            return True

    except Exception as e:
        logger.error(f"db_save_detection error: {e}")
        import traceback; traceback.print_exc()
        return False
