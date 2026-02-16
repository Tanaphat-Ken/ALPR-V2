from datetime import datetime, timedelta
from operator import and_
from uuid import uuid4
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from Configs.dbconfig import Base
from typing import List, Optional
from fastapi import status
from Models.user_subscription import UserSubscription
from Models.subscription import Subscription
from sqlalchemy.sql import func
import pytz
from sqlalchemy.exc import SQLAlchemyError
from Models.image_logs import ApiImageLogs
from Models.video_logs import VideoLogs
import sqlalchemy


class Token(Base):
    __tablename__ = "token"

    key = Column(String(255), primary_key=True, nullable=False)
    user_sub_id = Column(Integer, ForeignKey(
        "user_subscription.user_sub_id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), nullable=True)
    service_type = Column(String(50), nullable=True)
    expire_time = Column(TIMESTAMP, nullable=True)
    create_at = Column(TIMESTAMP, nullable=True)
    update_at = Column(TIMESTAMP, nullable=True)

    user_subscription = relationship(
        "UserSubscription", back_populates="tokens")
    api_image_logs = relationship("ApiImageLogs", back_populates="token")
    video_logs = relationship("VideoLogs", back_populates="token")

    @staticmethod
    async def get_tokens(user_id: int, service_type: str, db: AsyncSession) -> List['Token']:
        try:
            # Determine logic based on service_type
            criteria = []
            if service_type == 'API':
                criteria.append(Subscription.has_api_access == 1)
            elif service_type == 'WEBSOCKET':
                criteria.append(Subscription.has_websocket_access == 1)
            elif service_type == 'VIDEO_WEBSOCKET' or service_type == 'VIDEO':
                criteria.append(Subscription.has_video_upload == 1)
            elif service_type == 'RTSP':
                criteria.append(Subscription.has_rtsp_stream == 1)
            
            # If criteria is empty, we might return empty or error, 
            # or try to match service_type directly if needed (though unlikely with TIERs now)

            query_stmt = select(UserSubscription.user_sub_id).join(
                Subscription,
                UserSubscription.sub_id == Subscription.sub_id
            ).where(
                UserSubscription.user_id == user_id,
                UserSubscription.is_activate.is_(True)
            )

            if criteria:
                query_stmt = query_stmt.where(*criteria)
            else:
                # If no known service type, maybe try exact match as fallback (legacy behavior)
                query_stmt = query_stmt.where(Subscription.service_type == service_type)

            user_sub_id_query = query_stmt.limit(1)

            res = await db.execute(user_sub_id_query)
            user_sub_id = res.scalars().first()

            if not user_sub_id:
                # Instead of 404, return empty list if user has no subscription for this service
                # But original raised 404. Let's keep consistent but clearer message.
                # Actually, frontend expects 404? 
                # If no subscription, returns 404.
                raise Exception({
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "message": "User subscription not found for this service type"
                })

            query = select(Token).where(
                Token.user_sub_id == user_sub_id,
                Token.service_type == service_type
            )
            result = await db.execute(query)
            tokens = result.scalars().all()

            if not tokens:
                # Return empty list is better than 404 if subscription exists but no tokens?
                # But kept 404 to match original flow validation
                raise Exception({
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "message": "No tokens found"
                })

            return tokens

        except Exception as e:
            # Pass through the dict exception if it is one
            if isinstance(e.args[0], dict):
                 raise e
            raise Exception({
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            })

    @staticmethod
    async def new_token(user_id: int, service_type: str, token_name: str, expire_time: datetime, db: AsyncSession) -> 'Token':
        try:
            # Determine logic based on service_type
            criteria = []
            if service_type == 'API':
                criteria.append(Subscription.has_api_access == 1)
            elif service_type == 'WEBSOCKET':
                criteria.append(Subscription.has_websocket_access == 1)
            elif service_type == 'VIDEO_WEBSOCKET' or service_type == 'VIDEO':
                criteria.append(Subscription.has_video_upload == 1)
            elif service_type == 'RTSP':
                criteria.append(Subscription.has_rtsp_stream == 1)

            query_stmt = select(Subscription.token_limit, UserSubscription.user_sub_id).join(
                    Subscription,
                    UserSubscription.sub_id == Subscription.sub_id
                ).where(
                    UserSubscription.user_id == user_id,
                    UserSubscription.is_activate == True
                )
            
            if criteria:
                query_stmt = query_stmt.where(*criteria)
            else:
                query_stmt = query_stmt.where(Subscription.service_type == service_type)

            result = await db.execute(query_stmt.limit(1))

            row = result.first()
            if not row:
                 raise Exception(
                    {"status_code": status.HTTP_404_NOT_FOUND, "message": "No active subscription found for this service"})
            
            token_limit, user_sub_id = row
            
            # Handle NULL token_limit - set default to 5 if None
            if token_limit is None:
                token_limit = 5

            check_token_query = select(func.count(Token.key)).where(
                Token.user_sub_id == user_sub_id)
            result = await db.execute(check_token_query)
            token_count = result.scalar()

            if token_count >= token_limit:
                raise Exception(
                    {"status_code": status.HTTP_400_BAD_REQUEST, "message": "Number of tokens are at limit"})

            # Verify subscription exists (already checked above, but kept for consistency)
            # The feature flag check above already ensures the user has access to this service type

            token_name_query = select(Token).where(
                Token.user_sub_id == user_sub_id,
                Token.name == token_name
            )
            token_name_result = await db.execute(token_name_query)
            existing_token = token_name_result.scalars().first()

            if existing_token:
                raise Exception(
                    {"status_code": status.HTTP_400_BAD_REQUEST, "message": "Token name has already been used"})

            if expire_time < datetime.now():
                raise Exception(
                    {"status_code": status.HTTP_400_BAD_REQUEST, "message": "Expire time must be more than today"})

            if not expire_time:
                expire_time = datetime.now() + timedelta(days=30)

            new_token = Token(
                key=str(uuid4()),
                user_sub_id=user_sub_id,
                name=token_name,
                service_type=service_type,
                expire_time=expire_time,
                create_at=datetime.now(),
                update_at=datetime.now()
            )

            db.add(new_token)
            await db.commit()
            await db.refresh(new_token)
            return new_token

        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    async def update_token(key: str, token_name: Optional[str], expire_time: Optional[datetime], db: AsyncSession) -> 'Token':
        try:

            query = select(Token).where(Token.key == key)
            result = await db.execute(query)
            token = result.scalar_one_or_none()

            if not token:
                raise Exception(
                    {"status_code": status.HTTP_404_NOT_FOUND, "message": "Token not found"})

            if token_name:
                token_name_query = select(Token).where(
                    Token.name == token_name
                )

                token_name_result = await db.execute(token_name_query)
                existing_token = token_name_result.scalar_one_or_none()

                if existing_token:
                    raise Exception(
                        {"status_code": status.HTTP_400_BAD_REQUEST, "message": "Token name has already been used"})

            if expire_time and expire_time < datetime.today():

                raise Exception(
                    {"status_code": status.HTTP_400_BAD_REQUEST, "message": "Expire time must be more than today"})

            if token_name:
                token.name = token_name
            if expire_time:
                token.expire_time = expire_time

            token.update_at = datetime.now()

            await db.commit()

            await db.refresh(token)
            return token

        except Exception as e:
            raise e

    @staticmethod
    async def delete_token(key: str, db: AsyncSession) -> 'Token':
        try:
            find_image_log = select(ApiImageLogs).where(
                ApiImageLogs.token_key == key
            )

            result1 = await db.execute(find_image_log)
            image_logs = result1.scalars().all()

            # Delete each image log
            for image_log in image_logs:
                await db.delete(image_log)
            await db.commit()

            find_video_log = select(VideoLogs).where(
                VideoLogs.token_key == key
            )

            result2 = await db.execute(find_video_log)
            video_logs = result2.scalars().all()

            # Delete each video log
            for video_log in video_logs:
                await db.delete(video_log)
            await db.commit()

            query = select(Token).where(
                Token.key == key
            )
            result = await db.execute(query)
            token = result.scalar_one_or_none()

            if not token:
                raise Exception(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Token not found"
                )

            await db.delete(token)
            await db.commit()

            return {
                "detail": "Token was deleted successfully.",
                "status_code": status.HTTP_200_OK
            }

        except sqlalchemy.exc.ProgrammingError as e:
            # Log or handle the error
            print(f"Database error: {e}")

    @staticmethod
    async def get_token_usage(user_id: int, service_type: str, db: AsyncSession):
        try:
            # Map service_type (API, WEBSOCKET, etc.) to Subscription feature flags
            criteria = []
            if service_type == 'API':
                criteria.append(Subscription.has_api_access == 1)
            elif service_type == 'WEBSOCKET':
                criteria.append(Subscription.has_websocket_access == 1)
            elif service_type == 'VIDEO_WEBSOCKET' or service_type == 'VIDEO':
                criteria.append(Subscription.has_video_upload == 1)
            elif service_type == 'RTSP':
                criteria.append(Subscription.has_rtsp_stream == 1)

            # Step 1: Get user_sub_id for an active subscription
            sub_query = select(UserSubscription.user_sub_id).join(
                Subscription,
                UserSubscription.sub_id == Subscription.sub_id
            ).where(
                UserSubscription.user_id == user_id,
                UserSubscription.is_activate.is_(True)
            )

            if criteria:
                sub_query = sub_query.where(*criteria)
            else:
                sub_query = sub_query.where(Subscription.service_type == service_type)

            sub_result = await db.execute(sub_query.limit(1))
            user_sub_id = sub_result.scalar()
            if not user_sub_id:
                return []  # No active subscription

            # Step 2: Get all token names for the user_sub_id filtered by service_type
            token_query = select(Token.key, Token.name).where(
                Token.user_sub_id == user_sub_id,
                Token.service_type == service_type
            )
            token_result = await db.execute(token_query)
            token_map = {row[0]: row[1] for row in token_result.fetchall()}
            if not token_map:
                return []  # No tokens found

            # Step 3: Set up the time window (past 24 hours)
            now_utc = datetime.now(pytz.utc)
            bangkok_tz = pytz.timezone("Asia/Bangkok")
            now_bangkok = now_utc.astimezone(bangkok_tz)
            start_time = (now_bangkok - timedelta(hours=24)).replace(tzinfo=None)

            # Step 4: Query IMAGE logs (ApiImageLogs)
            usage_query = select(
                ApiImageLogs.token_key,
                ApiImageLogs.created_at
            ).where(
                ApiImageLogs.token_key.in_(token_map.keys()),
                ApiImageLogs.created_at >= start_time
            )
            usage_result = await db.execute(usage_query)
            usage_data = usage_result.fetchall()

            # Query VIDEO logs (VideoLogs)
            usage_video_query = select(
                VideoLogs.token_key,
                VideoLogs.created_at
            ).where(
                VideoLogs.token_key.in_(token_map.keys()),
                VideoLogs.created_at >= start_time
            )
            usage_video_res = await db.execute(usage_video_query)
            usage_video_data = usage_video_res.fetchall()

            # Step 5: Initialize 24-hour usage arrays for each token.
            token_usage = {key: [0] * 24 for key in token_map.keys()}
            token_usage_video = {key: [0] * 24 for key in token_map.keys()}

            # Helper function: Compute bucket index based on log timestamp.
            def get_bucket(log_time):
                if log_time.tzinfo is None:
                    log_time = bangkok_tz.localize(log_time)
                else:
                    log_time = log_time.astimezone(bangkok_tz)
                diff = now_bangkok - log_time
                bucket = int(diff.total_seconds() // 3600)
                return bucket

            # Populate IMAGE usage
            for token_key, created_at in usage_data:
                bucket = get_bucket(created_at)
                if 0 <= bucket < 24:
                    token_usage[token_key][bucket] += 1

            # Populate VIDEO usage
            for token_key, created_at in usage_video_data:
                bucket = get_bucket(created_at)
                if 0 <= bucket < 24:
                    token_usage_video[token_key][bucket] += 1

            # Step 6: Merge IMAGE and VIDEO usage
            merged_usage = {}
            for token in token_map.keys():
                image_usage = token_usage.get(token, [0] * 24)
                video_usage = token_usage_video.get(token, [0] * 24)
                merged_usage[token] = [img + vid for img, vid in zip(image_usage, video_usage)]

            # Step 7: Format the response with token_name instead of token_key
            response = [
                {"token_key": token_map[token], "usage_per_hour": merged_usage[token]}
                for token in token_map.keys()
            ]
            return response

        except Exception as e:
            raise Exception(f"Error processing API usage: {e}")

