from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from Configs.dbconfig import get_db
from Libs.except_err import response_exception
from typing import List, Dict, Any, Optional
from Models.subscription import Subscription
from sqlalchemy import select, insert, update
from Models.schemas_subscription import *
from Models.user_subscription import UserSubscription
from Models.users import User
import pytz
from dateutil.relativedelta import relativedelta

router = APIRouter()


@router.get("/get_all_service")
async def get_all_service(db: AsyncSession = Depends(get_db)):
    try:
        # Return Tier subscriptions — รองรับทั้ง "Tier X" และ "TIER_X" format
        query = select(Subscription).where(
            Subscription.service_type.ilike('tier%')
        )
        result = await db.execute(query)
        subscriptions = result.scalars().all()

        if not subscriptions:
            raise HTTPException(
                status_code=404,
                detail="No tier subscriptions found"
            )

        return [
            {
                "sub_id": s.sub_id,
                "service_type": s.service_type,
                "billing_period": s.billing_period,
                "price": s.price,
                "description": s.description,
                "api_request_limit": s.api_request_limit,
                "video_upload_limit": s.video_upload_limit,
                "has_api_access": s.has_api_access,
                "has_websocket_access": s.has_websocket_access,
                "has_video_upload": s.has_video_upload,
                "has_rtsp_stream": s.has_rtsp_stream,
                "token_limit": s.token_limit,
            }
            for s in subscriptions
        ]
    except HTTPException:
        raise
    except Exception as e:
        return response_exception(e)

@router.post("/create_user_subscription")
async def new_user_subscription(
    user_subscription: UserSubscriptionRequest,  # Pydantic model to handle the request body
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get the current time in Bangkok timezone (without timezone info)
        now_utc = datetime.now(pytz.utc)
        bangkok_tz = pytz.timezone("Asia/Bangkok")
        now_bangkok = now_utc.astimezone(bangkok_tz)
        time_now = now_bangkok.replace(tzinfo=None)

        # Query to check if the subscription exists
        query = select(Subscription).where(Subscription.sub_id == user_subscription.sub_id)
        result = await db.execute(query)
        sub_info = result.scalars().first()

        # Query to check if the user exists
        query = select(User).where(User.user_id == user_subscription.user_id)
        result = await db.execute(query)
        user_info = result.scalars().first()

        # Check if both subscription and user exist
        if sub_info and user_info:
            # Check if the user already has an active subscription for the same plan
            existing_subscription_query = select(UserSubscription).where(
                UserSubscription.user_id == user_info.user_id,
                UserSubscription.sub_id == sub_info.sub_id,
                UserSubscription.is_activate == True  # Check if active
            )
            existing_subscription_result = await db.execute(existing_subscription_query)
            existing_subscription = existing_subscription_result.scalars().first()

            if existing_subscription:
                # If there's already an active subscription, return a message
                return {"message": "User already has an active subscription for this plan."}

            # Now call check_billing_period with the correct billing period from sub_info
            end_date = check_billing_period(sub_info.billing_period, time_now)

            # Insert the new UserSubscription
            stmt = insert(UserSubscription).values(
                start_date=time_now,
                end_date=end_date,
                is_activate=True,
                request_quota=sub_info.api_request_limit,
                sub_id=sub_info.sub_id,
                user_id=user_info.user_id
            )

            await db.execute(stmt)
            await db.commit()

            return {"message": "Subscription successfully created for the user."}
        else:
            return {"message": "Either the user or the subscription plan was not found. Please verify the details and try again."}

    except Exception as e:
        return response_exception(e)
    
def check_billing_period(billing_period, start_date):
    if billing_period == "MONTHLY":
        end_date = start_date + relativedelta(months=1)
    elif billing_period == "QUARTERLY":
        end_date = start_date + relativedelta(months=3)
    elif billing_period == "SEMI ANNUALLY":
        end_date = start_date + relativedelta(months=6)
    else:
        end_date = start_date + relativedelta(months=12)
    
    return end_date

@router.get("/get_user_subscriptions/{user_id}", response_model=List[UserSubscriptionResponse])
async def get_user_subscriptions(
    user_id: int = Path(..., description="The ID of the user"),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Fetch user subscriptions including the related subscription details
        # Using join to get subscription details
        stmt = select(UserSubscription, Subscription).join(
            Subscription, UserSubscription.sub_id == Subscription.sub_id
        ).where(
            UserSubscription.user_id == user_id, 
            UserSubscription.is_activate == True
        )
        
        result = await db.execute(stmt)
        user_subs = result.all()
        
        response = []
        for user_sub, sub in user_subs:
            response.append(UserSubscriptionResponse(
                user_sub_id=user_sub.user_sub_id,
                is_activate=user_sub.is_activate,
                start_date=str(user_sub.start_date) if user_sub.start_date else None,
                end_date=str(user_sub.end_date) if user_sub.end_date else None,
                request_quota=user_sub.request_quota,
                subscription_details=SubscriptionDetailsResponse(
                    sub_id=sub.sub_id,
                    billing_period=sub.billing_period,
                    service_type=sub.service_type,
                    price=sub.price,
                    description=sub.description,
                    api_request_limit=sub.api_request_limit,
                    video_upload_limit=sub.video_upload_limit,
                    has_api_access=bool(sub.has_api_access),
                    has_websocket_access=bool(sub.has_websocket_access),
                    has_video_upload=bool(sub.has_video_upload),
                    has_rtsp_stream=bool(sub.has_rtsp_stream)
                )
            ))
            
        return response

    except Exception as e:
        # Log the error properly in a real app
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/change_subscription")
async def change_subscription(
    request: UserSubscriptionRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Get the new subscription details to know the service type
        new_sub_query = select(Subscription).where(Subscription.sub_id == request.sub_id)
        new_sub_result = await db.execute(new_sub_query)
        new_sub = new_sub_result.scalars().first()
        
        if not new_sub:
             raise HTTPException(status_code=404, detail="New subscription plan not found.")

        is_tier_plan = new_sub.service_type.upper().startswith("TIER")

        # 2. Find existing active subscriptions in the same plan family.
        # Tier plans should behave as a single bundle (only one active at a time).
        if is_tier_plan:
            find_existing_stmt = select(UserSubscription).join(Subscription).where(
                UserSubscription.user_id == request.user_id,
                Subscription.service_type.ilike('tier%'),
                UserSubscription.is_activate == True
            )
        else:
            find_existing_stmt = select(UserSubscription).join(Subscription).where(
                UserSubscription.user_id == request.user_id,
                Subscription.service_type == new_sub.service_type,
                UserSubscription.is_activate == True
            )

        existing_result = await db.execute(find_existing_stmt)
        existing_subs = existing_result.scalars().all()
        
        now_utc = datetime.now(pytz.utc)
        bangkok_tz = pytz.timezone("Asia/Bangkok")
        now_bangkok = now_utc.astimezone(bangkok_tz)
        time_now = now_bangkok.replace(tzinfo=None)
        
        end_date = check_billing_period(new_sub.billing_period, time_now)

        if any(existing_sub.sub_id == request.sub_id for existing_sub in existing_subs):
            return {"message": "User is already subscribed to this plan."}

        if existing_subs:
            existing_ids = [existing_sub.user_sub_id for existing_sub in existing_subs]
            stmt_update = update(UserSubscription).where(
                UserSubscription.user_sub_id.in_(existing_ids)
            ).values(is_activate=False)
            await db.execute(stmt_update)

        stmt_insert = insert(UserSubscription).values(
            user_id=request.user_id,
            sub_id=request.sub_id,
            is_activate=True,
            start_date=time_now,
            end_date=end_date,
            request_quota=new_sub.api_request_limit
        )
        await db.execute(stmt_insert)
        await db.commit()

        if existing_subs:
            return {"message": "Subscription changed successfully."}

        return {"message": "Subscription created successfully."}

    except Exception as e:
        await db.rollback()
        return response_exception(e)

@router.delete("/cancel_subscription/{user_sub_id}")
async def cancel_subscription(
    user_sub_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Check if subscription exists
        stmt = select(UserSubscription).where(
            UserSubscription.user_sub_id == user_sub_id
        )
        result = await db.execute(stmt)
        user_sub = result.scalars().first()
        
        if not user_sub:
            raise HTTPException(status_code=404, detail="User subscription not found.")
            
        # Deactivate
        stmt_update = update(UserSubscription).where(
            UserSubscription.user_sub_id == user_sub_id
        ).values(is_activate=False)
        await db.execute(stmt_update)
        await db.commit()
        
        return {"message": "Subscription cancelled successfully."}
        
    except Exception as e:
        await db.rollback()
        return response_exception(e)