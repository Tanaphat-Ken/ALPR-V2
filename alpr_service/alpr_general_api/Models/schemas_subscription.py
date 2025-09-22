from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SubscriptionDetailsResponse(BaseModel):
    sub_id: int
    billing_period: str
    service_type: str
    price: Optional[float]
    request_limit: Optional[int]
    description: Optional[str]


class UserSubscriptionResponse(BaseModel):
    user_sub_id: int
    is_activate: bool
    start_date: Optional[str]
    end_date: Optional[str]
    request_quota: Optional[int]
    subscription_details: SubscriptionDetailsResponse


class UserSubscriptionInfoResponse(BaseModel):
    user_id: int
    subscriptions: List[UserSubscriptionResponse]


class PaymentLogCreate(BaseModel):
    sub_id: int
    amount: float
    method: str
    user_id: int

class UserSubscriptionRequest(BaseModel):
    user_id: int
    sub_id: int