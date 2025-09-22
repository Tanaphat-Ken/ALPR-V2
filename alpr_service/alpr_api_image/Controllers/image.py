import os
import asyncio
import io
import datetime
from datetime import time

import httpx
import pytz
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image
from typing import Annotated

from Configs import configs
from Configs.dbconfig import get_db
from Libs.utilitys import send_img_model
from Models.token import Token
from Models.users import User
from Models.image_logs import ApiImageLogs
from Models.user_subscription import UserSubscription
from Models.schemas import ApiImageLogCreate
from Models.car_bbox import Car_bbox
from Models.plate_bbox import Plate_bbox
from Libs.logging import logger

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/test")
async def upload_image(test: str = "default_value"):
    return {"message": test}


async def save_image_log(data, user_id, file_name, token, db: AsyncSession):
    # Extract data from the model response
    bkk_time = pytz.timezone("Asia/Bangkok")
    current_time = datetime.datetime.now(bkk_time)
    current_time = current_time.replace(tzinfo=None)
    car_bbox = data.get("car_bbox")
    plate_bbox = data.get("plate_bbox")
    plate_id = data.get("plate_id")
    province = data.get("province")
    full_plate = data.get("full_plate")
    service_type = "API"
    format_flag = data.get("format_flag")

    res_car = None
    if car_bbox:
        res_car = await Car_bbox.process_car_bbox(car_bbox, db)

    res_plate = None
    if plate_bbox:
        res_plate = await Plate_bbox.process_plate_bbox(plate_bbox, db)

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
        "car_bbox_id": res_car["car_bbox_id"] if res_car != None else None,
        "plate_bbox_id": res_plate["plate_bbox_id"] if res_plate != None else None,
        "user_id": user_id,
        "created_at": current_time,
        "token_key": token
    }

    # Save the log
    return await ApiImageLogs.save_log(db, **log_data)


@router.post("/upload-image")
async def upload_image(
    token: Annotated[str, Depends(oauth2_scheme)],
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        bkk_time = pytz.timezone("Asia/Bangkok")
        current_time = datetime.datetime.now(bkk_time)
        current_time = current_time.replace(tzinfo=None)
        user_id = await Token.find_user(token, db)
        subscription_valid = await UserSubscription.validate_user_subscription(user_id, db)

        if not subscription_valid:
            raise HTTPException(
                status_code=403, detail="No active subscription or quota exceeded."
            )
        if file.content_type not in configs.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {configs.ALLOWED_IMAGE_TYPES}"
            )

        file_contents = await file.read()

        if len(file_contents) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 50 MB."
            )

        image = Image.open(io.BytesIO(file_contents))

        unique_filename = f"./Images/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
        base_name = unique_filename
        counter = 1

        while os.path.isfile(unique_filename):
            unique_filename = f"{base_name.rstrip('.jpg')}_{counter}.jpg"
            counter += 1

        file.seek(0)
        image = Image.open(io.BytesIO(file_contents))

        format_map = {
            "image/jpg": "JPEG",
            "image/jpeg": "JPEG",
            "image/png": "PNG"
        }
        image_format = format_map.get(file.content_type)
        if not image_format:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format: {file.content_type}"
            )

        # Save resized image in memory
        resized_image_bytes = io.BytesIO()
        # Explicitly set the format
        image.save(resized_image_bytes, format=image_format)
        # Reset pointer to the beginning of the file
        resized_image_bytes.seek(0)

        # Call the external function to send the resized image
        model_response = await send_file_to_model(
            file_contents=resized_image_bytes.read(),  # Pass the image bytes
            filename=file.filename,                   # Use the original filename
            content_type=file.content_type            # Use the original content type
        )

        # Save log entry in the database
        await save_image_log(model_response, user_id, unique_filename, token, db)

        # Return success response
        devalue = await UserSubscription.devalue_user_quota(user_id, db)

        if not devalue:
            raise HTTPException(
                status_code=403, detail="Quota have problems."
            )
        return JSONResponse(
            status_code=200,
            content={
                "message": "Image uploaded and processed successfully!",
                "model_response": model_response,
                "user_id": user_id,
                "filename": unique_filename
            }
        )

    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


async def send_file_to_model(file_contents: bytes, filename: str, content_type: str):
    # External API endpoint
    external_api_url = "http://plate-recognizer:5000/api/v1/image/process"

    # Prepare the multipart/form-data payload
    files = {
        'file': (filename, file_contents, content_type)
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
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
