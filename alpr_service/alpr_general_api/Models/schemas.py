from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime


class TokenRequest(BaseModel):
    user_id: int
    service_type: str

    @validator('service_type')
    def service_type_validator(cls, value):
        if not value.strip():
            raise ValueError('user_id must not be empty')
        return value


class TokenNew(BaseModel):
    user_id: int
    service_type: str
    token_name: str
    expire_time: Optional[datetime]

    @validator('token_name')
    def token_name_validator(cls, value):
        if not value.strip():
            raise ValueError('token_name must not be empty')
        return value

    @validator('service_type')
    def service_type_validator(cls, value):
        if not value.strip():
            raise ValueError('service_type must not be empty')
        return value

    @validator('service_type')
    def service_type_validator2(cls, value):
        if value != "API" and value != "WEBSOCKET" and value != "RTSP" and value != "VIDEO_WEBSOCKET":
            raise ValueError('service_type not in choice')
        return value

    class Config:
        orm_mode = True


class TokenUpdate(BaseModel):
    key: str
    token_name: Optional[str] = None
    expire_time: Optional[datetime] = None

    @validator('key')
    def key_validator(cls, value):
        if not value.strip():
            raise ValueError('key must not be empty')
        return value


class TokenResponse(BaseModel):
    key: Optional[str]
    user_sub_id: Optional[int]
    name: Optional[str]
    service_type: Optional[str]
    expire_time: Optional[datetime]

    class Config:
        orm_mode = True


class TokenKey(BaseModel):
    key: str

    @validator('key')
    def key_validator(cls, value):
        if not value.strip():
            raise ValueError('user_id must not be empty')
        return value
