from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocket, WebSocketException
from datetime import datetime, timezone
from Models.web_socket_token import Token
from Models.web_socket_users import User
from Models.web_socket_user_subscription import UserSubscription
from Models.web_socket_subscription import Subscription


async def validate_websocket_token(token: str, websocket: WebSocket, db_session: AsyncSession):
    try:
        # Print or log the token for debugging
        print(f"Token received: {token}")  # This will print to the console
        # This will log the token

        # Token validation logic
        query = select(Token).where(Token.key == token)
        result = await db_session.execute(query)
        token_record = result.scalars().first()

        if token_record:
            # Check token expiration
            token_expiry = token_record.expire_time.replace(
                tzinfo=timezone.utc)
            if token_expiry > datetime.now(timezone.utc):

                return token_record
            else:
                await websocket.send_text(f"Error in validate_websocket_token")
                await websocket.close(code=1008)
                raise WebSocketException(
                    status_code=401, detail="Token expired")
        else:
            await websocket.send_text(f"Error 401 in validate_websocket_token")
            await websocket.close(code=1008)
            raise WebSocketException(status_code=401, detail="Invalid token")
    except Exception as e:
        await websocket.send_text(f"Error in validate_websocket_token {e}")
        await websocket.close(code=1008)
        raise WebSocketException(
            status_code=500, detail="Internal server error")


async def validate_websocket_token_and_return_user(token: str, websocket: WebSocket, db_session: AsyncSession):
    try:
        # Print or log the token for debugging
        print(f"Token received: {token}")  # This will print to the console
        # This will log the token

        # Token validation logic
        query = select(Token).where(Token.key == token)
        result = await db_session.execute(query)
        token_record = result.scalars().first()

        if token_record:
            # Check token expiration
            token_expiry = token_record.expire_time.replace(
                tzinfo=timezone.utc)
            if token_expiry > datetime.now(timezone.utc):
                return token_record.user_id
            else:
                await websocket.close(code=1008)
                raise WebSocketException(
                    status_code=401, detail="Token expired")
        else:
            await websocket.close(code=1008)
            raise WebSocketException(status_code=401, detail="Invalid token")
    except Exception as e:
        await websocket.send_text(f"Error: Token validation failed. {e}")
