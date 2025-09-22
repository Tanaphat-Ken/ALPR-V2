from fastapi import HTTPException
from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, Time, ForeignKey
from Configs.dbconfig import Base
from sqlalchemy.orm import relationship
from datetime import datetime, time
from sqlalchemy.ext.asyncio import AsyncSession
from Models.car_bbox import Car_bbox
from Models.plate_bbox import Plate_bbox
# from Models.users import User
# from Models.token import Token


class ApiImageLogs(Base):
    __tablename__ = 'image_logs'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    score = Column(Integer, nullable=True)
    plate_id = Column(String(255), nullable=True)
    province = Column(String(255), nullable=True)
    service_type = Column(String(255), nullable=True)
    format_flag = Column(String(255), nullable=True)
    full_plate = Column(String(255), nullable=True)
    file_name = Column(String(255), nullable=True)
    processing_time = Column(Time, nullable=True)
    car_bbox_id = Column(Integer, ForeignKey(
        "car_bbox.car_bbox_id"), nullable=True)
    plate_bbox_id = Column(Integer, ForeignKey(
        "plate_bbox.plate_bbox_id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=True)
    token_key = Column(String(255), ForeignKey("token.key"),
                       nullable=True)  # Corrected data type

    # Relationships
    car_bbox = relationship("Car_bbox", back_populates="api_image_logs")
    plate_bbox = relationship("Plate_bbox", back_populates="api_image_logs")
    user = relationship("User", back_populates="api_image_logs")
    token = relationship("Token", back_populates="api_image_logs")

    @staticmethod
    async def save_log(db: AsyncSession, **kwargs):
        try:
            new_log = ApiImageLogs(**kwargs)
            db.add(new_log)

            # Commit the transaction to save the data
            await db.commit()

            # Refresh the instance to get the latest state (e.g., auto-generated IDs)
            await db.refresh(new_log)

            return new_log
        except Exception as e:
            await db.rollback()  # Rollback the transaction in case of an error
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save log: {str(e)}"
            )

    @classmethod
    async def create_log(cls, db: AsyncSession, **kwargs):
        try:
            new_log = cls(**kwargs)
            db.add(new_log)
            await db.commit()
            return new_log
        except Exception as e:
            await db.rollback()  # Rollback in case of error
            raise e
