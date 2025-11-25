from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, select, insert
from sqlalchemy.orm import relationship
from Configs.dbconfig import Base
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from Models.image_logs import ApiImageLogs
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
import pytz
import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    is_activate = Column(Boolean, nullable=False)
    created_at = Column(TIMESTAMP, nullable=True)
    updated_at = Column(TIMESTAMP, nullable=True)

    subscriptions = relationship(
        "UserSubscription", back_populates="user")
    payment_logs = relationship("PaymentLog", back_populates="user")
    subscription_logs = relationship(
        "SubscriptionLog", back_populates="user")
    api_image_logs = relationship("ApiImageLogs", back_populates="user")
    video_logs = relationship("VideoLogs", back_populates="user")

    @staticmethod
    async def get_user_info(user_id: int, db: AsyncSession):
        try:
            query = select(User).where(User.user_id == user_id)
            result = await db.execute(query)
            user_res = result.scalars().all()

            if not user_res:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No user found with the given ID"
                )

            return user_res
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @staticmethod
    async def new_user(email: str, password: str, db: AsyncSession):
        try:
            now_utc = datetime.datetime.now(pytz.utc)
            bangkok_tz = pytz.timezone("Asia/Bangkok")
            now_bangkok = now_utc.astimezone(bangkok_tz)
            time_now = now_bangkok.replace(tzinfo=None)

            # Checking if email already exists
            result = await db.execute(select(User).where(User.email == email))
            check_email = result.scalars().first()

            if check_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This email is already registered"
                )

            # Insert new user into the database
            stmt = insert(User).values(
                email=email, 
                password=password, 
                is_activate=True, 
                created_at=time_now, 
                updated_at=time_now
            ).returning(User.user_id, User.email)
            
            result = await db.execute(stmt)
            await db.commit()
            
            new_user_data = result.fetchone()
            
            return {
                "user_id": new_user_data[0],
                "email": new_user_data[1],
                "message": "User created successfully"
            }
        
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )
    
    @staticmethod
    async def get_user_by_email(email: str, db: AsyncSession):
        """Get user by email address"""
        try:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalars().first()
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    async def verify_user_password(email: str, password: str, db: AsyncSession):
        """Verify user credentials for login"""
        user = await User.get_user_by_email(email, db)
        
        if not user:
            return None
        
        # Verify password
        if not pwd_context.verify(password, user.password):
            return None
        
        # Check if user is active
        if not user.is_activate:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        return user