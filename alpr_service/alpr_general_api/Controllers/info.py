from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from Configs.dbconfig import get_db
from Models.schemas_user import UserInfo, UserInfoResponse
from Models.users import User
from Models.user_subscription import UserSubscription
from Models.subscription import Subscription
from Libs.except_err import response_exception
from Models.schemas_subscription import SubscriptionDetailsResponse, UserSubscriptionResponse, UserSubscriptionInfoResponse
import logging
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

router = APIRouter()


@router.get("/user/{user_id}", response_model=List[UserInfoResponse])
async def get_user_info(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await User.get_user_info(user_id, db)
    except Exception as e:
        response_exception({"status_code": 500, "message": str(e)})


@router.get("/subscribe/{user_id}", response_model=UserSubscriptionInfoResponse)
async def get_user_subscriptions(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Fetch user subscription details for a given user_id.
    """
    try:
        # Fetch user subscriptions with preloaded subscription details
        result = await db.execute(
            select(UserSubscription).options(selectinload(UserSubscription.subscription)).where(
                UserSubscription.user_id == user_id
            )
        )
        user_subscriptions = result.unique().scalars().all()

        if not user_subscriptions:
            raise HTTPException(
                status_code=404, detail="No subscriptions found for this user.")

        # Prepare the response
        subscriptions_response = [
            UserSubscriptionResponse(
                user_sub_id=sub.user_sub_id,
                is_activate=sub.is_activate,
                start_date=sub.start_date.isoformat() if sub.start_date else None,
                end_date=sub.end_date.isoformat() if sub.end_date else None,
                request_quota=sub.request_quota,
                subscription_details=SubscriptionDetailsResponse(
                    sub_id=sub.subscription.sub_id,
                    billing_period=sub.subscription.billing_period,
                    service_type=sub.subscription.service_type,
                    price=sub.subscription.price,
                    request_limit=sub.subscription.request_limit,
                    description=sub.subscription.description,
                ),
            )
            for sub in user_subscriptions
        ]

        return {"user_id": user_id, "subscriptions": subscriptions_response}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.error(f"Error occurred while fetching subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
