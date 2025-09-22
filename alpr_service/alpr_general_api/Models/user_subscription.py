from sqlalchemy import Column, Integer, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from Configs.dbconfig import Base
from Models.subscription import Subscription
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


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

    @classmethod
    async def get_user_subscriptions(cls, db: AsyncSession, user_id: int):
        result = await db.execute(
            select(cls).join(Subscription).where(cls.user_id == user_id)
        )
        return result.scalars().all()
