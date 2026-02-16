import logging
from fastapi import HTTPException, status
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from Configs.dbconfig import Base
# from Models.web_socket_subscription import Subscription
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocketException, WebSocket
from Models.web_socket_base import Base


class UserSubscription(Base):
    __tablename__ = "user_subscription"

    user_sub_id = Column(Integer, primary_key=True)
    is_activate = Column(Boolean, nullable=False)
    end_date = Column(Date, nullable=True)
    start_date = Column(Date, nullable=True)
    request_quota = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    sub_id = Column(Integer, ForeignKey("subscription.sub_id"), nullable=True)

    user = relationship("User", back_populates="subscriptions")
    subscription = relationship(
        "Subscription", back_populates="user_subscriptions")
    tokens = relationship("Token", back_populates="user_subscription")

    @staticmethod
    async def validate_user_subscription(user_id: int, db: AsyncSession):
        try:
            # Perform the query to find the active subscription for the user
            query = select(UserSubscription).where(
                UserSubscription.user_id == user_id,
                UserSubscription.is_activate == True,
                UserSubscription.request_quota > 0
            )
            logging.info(f"Executing query: {query}")
            result = await db.execute(query)
            subscription = result.scalar()

            if subscription is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No active subscription with available quota."
                )

            # Update the request_quota by decrementing it by 1
            # subscription.request_quota -= 1

            # Commit the change to the database
            db.add(subscription)
            await db.commit()

            return True

        except Exception as e:
            logging.error(f"Error validating and updating subscription: {e}")
            await db.rollback()  # Rollback in case of any error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error validating and updating subscription."
            )

    @staticmethod
    async def devalue_user_quota(user_id: int, db: AsyncSession):
        try:
            # Perform the query to find the active subscription for the user
            query = select(UserSubscription).where(
                UserSubscription.user_id == user_id,
                UserSubscription.is_activate == True,
                UserSubscription.request_quota > 0
            )
            logging.info(f"Executing query: {query}")
            result = await db.execute(query)
            subscription = result.scalar()

            if subscription is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No active subscription with available quota."
                )

            # Update the request_quota by decrementing it by 1
            subscription.request_quota -= 1

            # Commit the change to the database
            db.add(subscription)
            await db.commit()

            return True

        except Exception as e:
            logging.error(f"Error validating and updating subscription: {e}")
            await db.rollback()  # Rollback in case of any error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error validating and updating subscription."
            )

    @staticmethod
    async def validate_user_subscription_web_socket(user_id: int, websocket: WebSocket, db: AsyncSession):
        try:
            query = select(UserSubscription).join(
                Subscription,
                UserSubscription.sub_id == Subscription.sub_id
            ).where(
                UserSubscription.user_id == user_id,
                UserSubscription.is_activate == True,
                UserSubscription.request_quota > 0,
                Subscription.has_websocket_access == 1
            )

            result = await db.execute(query)
            subscription = result.scalar()
            if subscription is None:
                await websocket.send_text("No active subscription")
                raise WebSocketException("No active subscription")

            await websocket.send_text(f"Subscription valid. Remaining quota: {subscription.request_quota}")
            db.add(subscription)
            await db.commit()

        except WebSocketException as e:
            await db.rollback()
            await websocket.send_text(f"Error: Subscription update failed: {e}")
            raise

    @staticmethod
    async def devalue_user_quota_web_socket(user_id: int, websocket: WebSocket, db: AsyncSession):
        try:
            query = select(UserSubscription).join(
                Subscription,
                UserSubscription.sub_id == Subscription.sub_id
            ).where(
                UserSubscription.user_id == user_id,
                UserSubscription.is_activate == True,
                UserSubscription.request_quota > 0,
                Subscription.has_websocket_access == 1
            )

            result = await db.execute(query)
            subscription = result.scalar()
            if subscription is None:
                await websocket.send_text("No active subscription with WebSocket access")
                raise WebSocketException("No active subscription with WebSocket access")

            # Decrement request_quota
            subscription.request_quota -= 1
            await websocket.send_text(f"Quota deducted. Remaining: {subscription.request_quota}")
            db.add(subscription)
            await db.commit()

        except WebSocketException as e:
            await db.rollback()
            await websocket.send_text(f"Error: Quota deduction failed: {e}")
            raise
