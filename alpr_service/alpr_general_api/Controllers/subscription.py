from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from Configs.dbconfig import get_db
from Libs.except_err import response_exception
from typing import List, Dict, Any
from Models.subscription import Subscription
from sqlalchemy import select, insert
from fastapi import Query
from Models.schemas_subscription import UserSubscriptionRequest
from Models.user_subscription import UserSubscription
from Models.users import User
import pytz
import datetime
from dateutil.relativedelta import relativedelta

router = APIRouter()


@router.get("/get_all_service")
async def get_all_service(db: AsyncSession = Depends(get_db)):
    try:
        res = await Subscription.get_all_subscription(db)
        return res
    except Exception as e:
        return response_exception(e)

@router.post("/create_user_subscription")
async def new_user_subscription(
    user_subscription: UserSubscriptionRequest,  # Pydantic model to handle the request body
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get the current time in Bangkok timezone (without timezone info)
        now_utc = datetime.datetime.now(pytz.utc)
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
                request_quota=sub_info.request_limit,
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