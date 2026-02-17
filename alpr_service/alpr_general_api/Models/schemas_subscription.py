from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SubscriptionDetailsResponse(BaseModel):
    sub_id: int
    billing_period: str
    service_type: str
    price: Optional[float]
    description: Optional[str]
    api_request_limit: Optional[int]
    video_upload_limit: Optional[int]
    has_api_access: Optional[bool]
    has_websocket_access: Optional[bool]
    has_video_upload: Optional[bool]
    has_rtsp_stream: Optional[bool]


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