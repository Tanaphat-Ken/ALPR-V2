from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from Configs.dbconfig import get_db
import logging
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from Models.users import User
from Models.schemas_user import UserCreateRequest
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()


@router.post("/create_user")
async def  new_user(user: UserCreateRequest , db: AsyncSession = Depends(get_db)):
    try:
        hashed_password = pwd_context.hash(user.password)
        return await User.new_user(user.email, hashed_password, db)
        # return {"email": user.email,"password":hashed_password}
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error : {e}"
        )