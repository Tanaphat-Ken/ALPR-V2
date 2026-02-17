from sqlalchemy import Column, Integer, String, Float, TIMESTAMP
from sqlalchemy.orm import relationship
from Configs.dbconfig import Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import status
# from Models.user_subscription import UserSubscription


class Subscription(Base):
    __tablename__ = "subscription"

    sub_id = Column(Integer, primary_key=True)
    billing_period = Column(String(255), nullable=False)
    service_type = Column(String(255), nullable=False) # e.g., 'TIER_1', 'TIER_2', 'TIER_3'
    price = Column(Float, nullable=True)
    description = Column(String(255), nullable=True)
    
    # Quotas and Limits
    api_request_limit = Column(Integer, default=0)
    video_upload_limit = Column(Integer, default=0)
    
    # Feature Flags
    has_api_access = Column(Integer, default=0) # Using Integer as Boolean (0/1) for compatibility
    has_websocket_access = Column(Integer, default=0)
    has_video_upload = Column(Integer, default=0)
    has_rtsp_stream = Column(Integer, default=0)
    token_limit = Column(Integer, default=5)
    
    created_at = Column(TIMESTAMP, nullable=True)
    updated_at = Column(TIMESTAMP, nullable=True)


    user_subscriptions = relationship(
        "UserSubscription", back_populates="subscription")

    @staticmethod
    async def get_all_subscription(db: AsyncSession):
        query = select(Subscription)
        result = await db.execute(query)
        subscriptions = result.scalars().all()

        if not subscriptions:
            raise Exception({
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "No tokens found"
            })

        return subscriptions
