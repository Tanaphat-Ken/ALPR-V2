from pydantic import BaseModel, validator, EmailStr
from typing import Optional
from datetime import datetime


class UserInfo(BaseModel):
    user_id: int


class UserInfoResponse(BaseModel):
    user_id: int
    email: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class UserCreateRequest(BaseModel):
    email: str  
    password: str