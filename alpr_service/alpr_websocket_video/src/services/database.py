import pytz
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from src.constants.configs import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
from src.utils.logging import logger

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=False)

async_session_fatory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def insert_bbox(session, table_name, bbox):
    query = text(f"""
      INSERT INTO {table_name} (
        top_left_x, 
        top_left_y, 
        top_right_x, 
        top_right_y, 
        bottom_left_x, 
        bottom_left_y, 
        bottom_right_x, 
        bottom_right_y
      )
      VALUES (
        :top_left_x, 
        :top_left_y, 
        :top_right_x, 
        :top_right_y, 
        :bottom_left_x, 
        :bottom_left_y, 
        :bottom_right_x, 
        :bottom_right_y
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

async def commit_websocket_log(response, token, user_id, file_name="dummy_name"):
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

    async with async_session_fatory() as session:
      if car_bbox:
        car_bbox_id = await insert_bbox(session, 'car_bbox', car_bbox)
      if plate_bbox:
        plate_bbox_id = await insert_bbox(session, 'plate_bbox', plate_bbox)

      query = text("""
        INSERT INTO video_logs (plate_id, file_name, car_bbox_id, plate_bbox_id, user_id, province, full_plate, format_flag, token_key, created_at)
        VALUES (:plate_id, :file_name, :car_bbox_id, :plate_bbox_id, :user_id, :province, :full_plate, :format_flag, :token_key, :created_at)
      """)
      await session.execute(query, {
        'plate_id': plate_id,
        'file_name': file_name,
        'car_bbox_id': car_bbox_id,
        'plate_bbox_id': plate_bbox_id,
        'user_id': user_id,
        'province': province,
        'full_plate': full_plate,
        'format_flag': format_flag,
        'token_key': token,
        'created_at': created_at.replace(tzinfo=None)
      })

      await session.commit()

  except Exception as e:
    logger.error(f"Database error: {e}")
    if 'session' in locals():
      await session.rollback()

async def test_db_connection():
  async with async_session_fatory() as session:
    result = await session.execute(text("SELECT 1"))
    logger.info(result.fetchall())

async def get_user_id_with_token(token_key: str):
  async with async_session_fatory() as session:
    query = text("""     
      SELECT us.user_id, t.service_type, t.expire_time, us.is_activate 
      FROM token as t 
      LEFT JOIN user_subscription AS us ON us.user_sub_id = t.user_sub_id 
      LEFT JOIN subscription AS sub ON sub.sub_id = us.sub_id
      WHERE t.key = :token_key
    """)
    result = await session.execute(query, { "token_key": token_key })
    token_data = result.fetchone() 

    if not token_data:
      raise ValueError("Invalid token")

    user_id, service_type, expire_time, service_status = token_data

    if not service_status:
      raise ValueError("Your subscription is expired")

    if user_id is None:
      raise ValueError("Invalid token")

    if service_type != "VIDEO_WEBSOCKET":
      raise ValueError("Invalid token")

    if expire_time and expire_time < datetime.now():
      raise ValueError("Token is expired")

  return user_id