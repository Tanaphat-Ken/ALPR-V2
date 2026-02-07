import logging
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, WebSocketException, Depends
from Configs.dbconfig import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from Middlewares.web_socket_token_auth import validate_websocket_token, validate_websocket_token_and_return_user
import os
from PIL import Image
import io
import queue
import asyncio
import httpx
# from Models.web_socket_user_subscription import UserSubscription
from Models.web_socket_api_image_logs import ApiImageLogs
from Models.web_socket_token import Token
from datetime import time, datetime
from Models.plate_bbox import Plate_bbox
from Models.car_bbox import Car_bbox
from dotenv import load_dotenv
import pytz
router = APIRouter()

load_dotenv()
CLIENT_QUEUES = {}
MAX_IMAGE_SIZE_MB = 50  # Max size in MB
IMAGE_SIZE_LIMIT = MAX_IMAGE_SIZE_MB * 1024 * 1024  # Convert MB to bytes
TARGET_IMAGE_SIZE = (1920, 1200)  # Resize to 400x400
TIME = pytz.timezone(os.getenv("TIME_ZONE"))
current_time = datetime.now(TIME)
current_time = current_time.replace(tzinfo=None)


@router.websocket("/uploads")
async def websocket_endpoint(websocket: WebSocket, db_session: AsyncSession = Depends(get_db)):

    await websocket.accept()
    try:
        # Extract the Authorization header
        # Use WebSocket object ID as the client identifier
        TIME = pytz.timezone(os.getenv("TIME_ZONE"))
        current_time = datetime.now(TIME)
        current_time = current_time.replace(tzinfo=None)
        client_id = id(websocket)
        CLIENT_QUEUES[client_id] = asyncio.Queue()
        token = websocket.headers.get('Authorization')

        if not token:
            await websocket.send_text("Error: Authorization token missing")
            return  # Return to prevent further processing

        if not token.startswith("Bearer "):
            await websocket.send_text("Error: Authorization token bearer missing")
            return  # Return to prevent further processing

        # Extract the actual token value and validate it
        token_value = token.split("Bearer ")[1]
        await validate_websocket_token(token_value, websocket, db_session)

        user_id, email = await Token.find_user(token_value, db_session)
        await websocket.send_text(f"Token : {token_value} Email : {email}")
    except Exception as e:
        # Log the error and close the WebSocket
        print(f"Authorization error: {e}")
        # Close without sending further message
        return  # Ensure no further code is executed after close

    if not os.path.exists('./images'):
        os.makedirs('./images')

    try:
        while True:

            data = await websocket.receive_bytes()
            if len(data) > IMAGE_SIZE_LIMIT:
                await websocket.send_text(f"Error: Image size exceeds {MAX_IMAGE_SIZE_MB} MB")
                await websocket.close(code=413)  # Payload Too Large
                return

            image = Image.open(io.BytesIO(data))
            # resized_image = image.resize(TARGET_IMAGE_SIZE)

            filename = f"resized_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join('./images', filename)

            # Add the file path to the client-specific queue
            await CLIENT_QUEUES[client_id].put(filepath)
            image.save(filepath, format='PNG')

            await websocket.send_text(f"Image resized and saved as {filename}")

            if not CLIENT_QUEUES[client_id].empty():
                # Get the file path from the queue
                image_path = await CLIENT_QUEUES[client_id].get()

                try:
                    # Read file contents to send to the external model API
                    with open(image_path, "rb") as f:
                        file_contents = f.read()

                    # Send the file to the external model
                    result = await send_file_to_model(
                        file_contents=file_contents,
                        filename=filename,
                        content_type="image/png"
                    )

                    # await websocket.send_text(f"T1 : {datetime.now()}")
                    # await websocket.send_text(f"T2 : {current_time}")
                    # await websocket.send_text(f"Model API response: {result}")
                    # await websocket.send_text(f"Model API response: {user_id}")
                    # await websocket.send_text(f"Model API response: {filename}")
                    # await websocket.send_text(f"Model API response: {token_value}")
                    res = await save_image_log(result, user_id, filename, token_value, db_session)

                    # Notify the client of the processing result
                    await websocket.send_text(f"Model API response: {str(res)}")

                except Exception as e:
                    await websocket.send_text(f"Error sending image to model: {str(e)}")

    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        # Close the database session when the WebSocket disconnects
        await db_session.close()


async def send_to_model(image_path: str):
    # Perform any async operations here, like calling an external API
    return "Image processed successfully"


async def send_file_to_model(file_contents: bytes, filename: str, content_type: str):
    # External API endpoint
    external_api_url = "http://localhost:5000/api/v1/image/process"
    # external_api_url = "http://plate-recognizer:5000/api/v1/image/process"

    # Prepare the multipart/form-data payload
    files = {
        'file': (filename, file_contents, content_type)
    }

    try:
        async with httpx.AsyncClient() as client:
            # Send the POST request to the external model API
            response = await client.post(external_api_url, files=files)
            response.raise_for_status()  # Raise exception for HTTP errors
            return response.json()  # Return the JSON response from the API
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send file to model: {str(e)}"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Model API returned an error: {e.response.text}"
        )


async def save_image_log(data, user_id, file_name, token, db: AsyncSession):
    # Extract data from the model response
    logging.info(f"test :")
    car_bbox = data.get("car_bbox")
    plate_bbox = data.get("plate_bbox")
    plate_id = data.get("plate_id")
    province = data.get("province")
    full_plate = data.get("full_plate")
    service_type = "WEBSOCKET"
    format_flag = data.get("format_flag")

    # Process car_bbox if available (new pipeline may not have car detection)
    car_bbox_id = None
    if car_bbox:
        res_car = await Car_bbox.process_car_bbox(car_bbox, db)
        car_bbox_id = res_car["car_bbox_id"]
        print(f"Car : {res_car}")
    else:
        print("No car_bbox in response (new ALPR pipeline - full image mode)")

    # Process plate_bbox (required)
    if not plate_bbox:
        raise ValueError("plate_bbox is missing in the data.")
    res_plate = await Plate_bbox.process_plate_bbox(plate_bbox, db)
    print(f"plate : {res_plate}")

    # Prepare the log data
    log_data = {
        "score": 50,
        "plate_id": plate_id,
        "province": province,
        "service_type": service_type,
        "format_flag": format_flag,
        "full_plate": full_plate,
        "file_name": file_name,
        "processing_time": time(0, 1, 30),
        "car_bbox_id": car_bbox_id,  # Can be None for new pipeline
        "plate_bbox_id": res_plate["plate_bbox_id"],
        "user_id": user_id,
        "created_at": current_time,
        "token_key": token
    }

    # Save the log
    await ApiImageLogs.save_log(db, **log_data)
    return log_data
