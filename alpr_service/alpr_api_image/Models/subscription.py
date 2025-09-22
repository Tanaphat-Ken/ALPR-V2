from sqlalchemy import Column, Integer, String, Float, TIMESTAMP
from sqlalchemy.orm import relationship
from Configs.dbconfig import Base
# from Models.user_subscription import UserSubscription


class Subscription(Base):
    __tablename__ = "subscription"

    sub_id = Column(Integer, primary_key=True)
    billing_period = Column(String(255), nullable=False)
    service_type = Column(String(255), nullable=False)
    price = Column(Float, nullable=True)
    request_limit = Column(Integer, nullable=True)
    description = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, nullable=True)
    updated_at = Column(TIMESTAMP, nullable=True)

    user_subscriptions = relationship(
        "UserSubscription", back_populates="subscription")
