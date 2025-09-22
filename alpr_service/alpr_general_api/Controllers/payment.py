from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from Configs.dbconfig import get_db
from Models.payment_logs import PaymentLog
from Models.subscription_logs import SubscriptionLog
from Models.schemas_subscription import PaymentLogCreate
from Models.subscription import Subscription
import pytz
import datetime

router = APIRouter()
TIME = pytz.timezone("Asia/Bangkok")
current_time = datetime.datetime.now(TIME)
current_time = current_time.replace(tzinfo=None)


@router.post("/payment_logs")
async def create_payment_log(payment_data: PaymentLogCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscription.service_type, Subscription.price, Subscription.request_limit).where(Subscription.sub_id == payment_data.sub_id))
    subscription_data = result.first()

    if not subscription_data:
        raise HTTPException(status_code=404, detail="Subscription not found")

    service_type, price, request_limit = subscription_data

    new_payment_log = PaymentLog(
        amount=payment_data.amount,
        method=payment_data.method,
        user_id=payment_data.user_id
    )

    db.add(new_payment_log)
    await db.commit()
    await db.refresh(new_payment_log)

    new_subscription_logs = SubscriptionLog(
        transection_id=new_payment_log.transection_id,
        request_limit=request_limit,
        price=price,
        service_type=service_type,
        user_id=payment_data.user_id,
        created_at=current_time
    )
    db.add(new_subscription_logs)
    await db.commit()
    await db.refresh(new_subscription_logs)

    return new_subscription_logs


@router.get("/subscription_logs")
async def get_subscription_logs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionLog))
    return result.scalars().all()
