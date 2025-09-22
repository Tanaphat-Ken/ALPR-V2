from sqlalchemy import Column, Integer, ForeignKey, Float, String, TIMESTAMP
from sqlalchemy.orm import relationship
from Configs.dbconfig import Base


class SubscriptionLog(Base):
    __tablename__ = "subscription_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    transection_id = Column(Integer, ForeignKey(
        "payment_logs.transection_id"), nullable=True)
    request_limit = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)
    service_type = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    created_at = Column(TIMESTAMP, nullable=True)

    user = relationship("User", back_populates="subscription_logs")
    payment_log = relationship(
        "PaymentLog", back_populates="subscription_logs")
