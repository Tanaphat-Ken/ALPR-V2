from fastapi import WebSocketDisconnect, WebSocketException, status
from sqlalchemy import Column, String, Integer, TIMESTAMP, ForeignKey, select
from sqlalchemy.orm import relationship
from Models.web_socket_base import Base
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from Models.web_socket_user_subscription import UserSubscription
from Models.web_socket_users import User


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

    # String-based relationship to avoid circular imports

    api_image_logs = relationship("ApiImageLogs", back_populates="token")
    user_subscription = relationship(
        "UserSubscription", back_populates="tokens")

    @staticmethod
    async def find_user(token: str, db: AsyncSession) -> int:
        try:
            # Perform the database query to find the token and user_id
            query = select(Token.user_sub_id).where(Token.key == token)
            logging.info(f"Executing query: {query}")
            result = await db.execute(query)

            # Log the query result for debugging
            logging.info(f"Query result: {result}")

            user_sub_id = result.scalar()
            query = select(UserSubscription.user_id).where(
                UserSubscription.user_sub_id == user_sub_id)
            result = await db.execute(query)
            user_id = result.scalar()
            query2 = select(User.email).where(
                User.user_id == user_id)
            result = await db.execute(query2)
            email = result.scalar()

            logging.info(f"User Email from token: {email}")

            # If no user_id found (None), raise a 404 error
            if user_id is None:
                logging.error("No user associated with this token.")
                raise WebSocketException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No user associated with this token"
                )

            return user_id, email  # Returning user_id
        except WebSocketDisconnect:
            print("Client disconnected")
