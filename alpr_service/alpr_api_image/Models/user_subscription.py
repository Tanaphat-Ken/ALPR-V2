import logging
from fastapi import HTTPException, status
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from Configs.dbconfig import Base
from Models.subscription import Subscription
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocketException, WebSocket


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
            # NULL request_quota = unlimited (Tier 3)
            # Only validate subscriptions that have API access
            from sqlalchemy import or_
            from sqlalchemy.orm import joinedload
            query = (
                select(UserSubscription)
                .join(UserSubscription.subscription)
                .where(
                    UserSubscription.user_id == user_id,
                    UserSubscription.is_activate == True,
                    Subscription.has_api_access == 1,
                    or_(UserSubscription.request_quota == None, UserSubscription.request_quota > 0),
                )
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
            # NULL request_quota = unlimited (Tier 3)
            # Only deduct from subscriptions that have API access
            from sqlalchemy import or_
            query = (
                select(UserSubscription)
                .join(UserSubscription.subscription)
                .where(
                    UserSubscription.user_id == user_id,
                    UserSubscription.is_activate == True,
                    Subscription.has_api_access == 1,
                    or_(UserSubscription.request_quota == None, UserSubscription.request_quota > 0),
                )
            )
            logging.info(f"Executing query: {query}")
            result = await db.execute(query)
            subscription = result.scalar()

            if subscription is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No active subscription with available quota."
                )

            # Only decrement if quota is not unlimited (NULL = Tier 3)
            if subscription.request_quota is not None:
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
            from sqlalchemy import or_
            query = select(UserSubscription).where(
                UserSubscription.user_id == user_id,
                UserSubscription.is_activate == True,
                or_(UserSubscription.request_quota == None, UserSubscription.request_quota > 0)
            )

            result = await db.execute(query)
            subscription = result.scalar()
            if subscription is None:
                await websocket.send_text("No active subscription")
                raise WebSocketException("No active subscription")

            # Decrement request_quota
            # subscription.request_quota -= 1
            await websocket.send_text(f"Subscription updated. Remaining quota: {subscription.request_quota}")
            # No need to start a new transaction manually, just add and commit
            db.add(subscription)
            # Commit the transaction
            await db.commit()
            # Notify the client

        except WebSocketException as e:
            await db.rollback()

            await websocket.send_text(f"Error: Subscription update failed: {e}")
            raise

    @staticmethod
    async def devalue_user_quota_web_socket(user_id: int, websocket: WebSocket, db: AsyncSession):
        try:
            from sqlalchemy import or_
            query = select(UserSubscription).where(
                UserSubscription.user_id == user_id,
                UserSubscription.is_activate == True,
                or_(UserSubscription.request_quota == None, UserSubscription.request_quota > 0)
            )

            result = await db.execute(query)
            subscription = result.scalar()
            if subscription is None:
                await websocket.send_text("No active subscription")
                raise WebSocketException("No active subscription")

            # Only decrement if quota is not unlimited (NULL = Tier 3)
            if subscription.request_quota is not None:
                subscription.request_quota -= 1
            await websocket.send_text(f"Subscription updated. Remaining quota: {subscription.request_quota}")
            # No need to start a new transaction manually, just add and commit
            db.add(subscription)
            # Commit the transaction
            await db.commit()
            # Notify the client

        except WebSocketException as e:
            await db.rollback()

            await websocket.send_text(f"Error: Subscription update failed: {e}")
            raise
