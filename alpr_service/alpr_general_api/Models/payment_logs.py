from sqlalchemy import Column, Integer, ForeignKey, String, TIMESTAMP
from sqlalchemy.orm import relationship
from Configs.dbconfig import Base


class PaymentLog(Base):
    __tablename__ = "payment_logs"
    transection_id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, nullable=True)
    method = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    created_at = Column(TIMESTAMP, nullable=True)

    subscription_logs = relationship(
        "SubscriptionLog", back_populates="payment_log")
    user = relationship("User", back_populates="payment_logs")
