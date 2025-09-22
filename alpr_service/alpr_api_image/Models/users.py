from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from Configs.dbconfig import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    is_activate = Column(Boolean, nullable=False)
    created_at = Column(TIMESTAMP, nullable=True)
    updated_at = Column(TIMESTAMP, nullable=True)

    # Use string-based lazy relationships to avoid circular import issues
    subscriptions = relationship("UserSubscription", back_populates="user")
    api_image_logs = relationship("ApiImageLogs", back_populates="user")
