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
    email: EmailStr
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    message: str = "Login successful"


class UserRegisterResponse(BaseModel):
    user_id: int
    email: str
    message: str = "Registration successful"


class UserCreateResponse(BaseModel):
    message: str
    user_id: Optional[int] = None
    email: Optional[str] = None