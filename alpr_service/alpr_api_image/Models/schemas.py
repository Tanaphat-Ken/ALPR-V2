from pydantic import BaseModel, Field
from typing import Optional
from datetime import time


class ApiImageLogCreate(BaseModel):
    score: int
    plate: str = Field(..., max_length=255)
    file_name: str = Field(..., max_length=255)
    processing_time: time
    x_max: float
    y_min: float
    x_min: float
    y_max: float
    user_id: Optional[int]  # user_id can be optional if needed

    class Config:
        orm_mode = True  # This is important if you need to convert from SQLAlchemy models to Pydantic models
