from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from Configs.dbconfig import get_db
from Models.token import Token
from Models.schemas import TokenResponse, TokenRequest, TokenNew, TokenUpdate, TokenKey
from Models.users import User  # Have to import if delete will 500 internal
from Libs.except_err import response_exception
from typing import List, Dict, Any
import pytz

router = APIRouter()


@router.get("/tokens/{user_id}", response_model=List[TokenResponse])
async def get_tokens(user_id: int = Path(...), service_type: str = Query(...), db: AsyncSession = Depends(get_db)):
    try:
        return await Token.get_tokens(user_id, service_type, db)
    except Exception as e:
        response_exception(e)

@router.post("/tokens", response_model=TokenResponse)
async def create_token(token_data: TokenNew, db: AsyncSession = Depends(get_db)):
    try:
        if token_data.expire_time == None:
            token_data.expire_time = datetime.today() + timedelta(days=30)
        token = await Token.new_token(
            user_id=token_data.user_id,
            service_type=token_data.service_type,
            token_name=token_data.token_name,
            expire_time=token_data.expire_time.replace(tzinfo=None),
            db=db
        )

        return token
    except Exception as e:
        response_exception(e)


@router.put("/tokens", response_model=TokenResponse)
async def update_token(token_data: TokenUpdate, db: AsyncSession = Depends(get_db)):
    try:
        token = await Token.update_token(
            key=token_data.key,
            token_name=token_data.token_name,
            expire_time=token_data.expire_time,
            db=db
        )
        return token
    except Exception as e:
        response_exception(e)


@router.delete("/tokens")
async def delete(token_data: TokenKey, db: AsyncSession = Depends(get_db)):
    try:

        res = await Token.delete_token(
            key=token_data.key,
            db=db
        )
        return res
    except Exception as e:
        response_exception(e)


@router.post("/tokens_usage_per_hour", response_model=List[Dict[str, Any]])
async def token_usage(token_data: TokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        res = await Token.get_token_usage(
            token_data.user_id, token_data.service_type, db)

        return res
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing API usage: {e}"
        )
