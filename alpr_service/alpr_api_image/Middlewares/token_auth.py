from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from Models.token import Token
from datetime import datetime, timezone
from fastapi.responses import JSONResponse
from Libs.logging import logger
current_time = datetime.now(timezone.utc)


class TokenAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, db_url):
        super().__init__(app)
        self.async_engine = create_async_engine(db_url)
        self.AsyncSession = sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False)

    async def dispatch(self, request: Request, call_next):
        db_session = None
        try:
            db_session = self.AsyncSession()
            request.state.db = db_session

            token = request.headers.get('Authorization')
            if not token:
                raise HTTPException(
                    status_code=401, detail="Authorization token missing")
            if not token.startswith("Bearer "):
                raise HTTPException(
                    status_code=401, detail="Invalid token format")
            token_value = token.split("Bearer ")[1]
            is_valid_token = await self.validate_token(token_value, request)
            if not is_valid_token:
                raise HTTPException(
                    status_code=401, detail="Invalid or expired token")

            response = await call_next(request)
            return response

        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={ "detail": str(e) })
        except Exception as e:
            return JSONResponse(status_code=500, content={ "detail": str(e) })
        finally:
            if db_session:
                await db_session.close()

    async def validate_token(self, token: str, request: Request) -> bool:
        db_session: AsyncSession = request.state.db
        try:
            query = select(Token).where(Token.key == token)
            result = await db_session.execute(query)
            token_record = result.scalars().first()
            if token_record:
                token_expiry = token_record.expire_time.replace(
                    tzinfo=timezone.utc)
                if token_expiry > datetime.now(timezone.utc):
                    logger.info(f"Token found and valid: {token_record.key}")
                    return True
                else:
                    logger.info(
                        f"Token is expired: {token_record.expire_time}")
            else:
                logger.info(f"Token not found: {token}")
            return False
        except Exception as e:
            logger.error(f"Error during token validation: {str(e)}")
            return e
