import logging
from sqlalchemy import Table, Column, String, MetaData, Integer, TIMESTAMP, ForeignKey, CheckConstraint
from Configs.dbconfig import Base
from fastapi import status, HTTPException
from sqlalchemy.orm import relationship
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from Models.user_subscription import UserSubscription


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
            logging.info(f"User ID from token: {user_id}")

            # If no user_id found (None), raise a 404 error
            if user_id is None:
                logging.error("No user associated with this token.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No user associated with this token"
                )

            return user_id  # Returning user_id
        except Exception as e:
            # Log the actual error for debugging
            logging.error(f"Error in find_user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error finding user ID: {str(e)}"
            )
