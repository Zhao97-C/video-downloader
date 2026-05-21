from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.services.payment import create_checkout_session, verify_webhook

router = APIRouter()


@router.post("/create-checkout")
async def create_checkout(
    plan: str = "monthly",
    current_user: dict = Depends(get_current_user),
):
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Payment not configured")

    price_id = (
        settings.STRIPE_PRO_MONTHLY_PRICE_ID if plan == "monthly"
        else settings.STRIPE_PRO_YEARLY_PRICE_ID
    )

    url = await create_checkout_session(
        user_email=current_user["email"],
        price_id=price_id,
        success_url="http://localhost:5173/pricing?success=true",
        cancel_url="http://localhost:5173/pricing?canceled=true",
    )
    return {"checkout_url": url}


@router.post("/webhook")
async def webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = verify_webhook(payload, sig_header)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_email")
        if customer_email:
            result = await db.execute(select(User).where(User.email == customer_email))
            user = result.scalar_one_or_none()
            if user:
                user.is_pro = True
                user.stripe_customer_id = session.get("customer")
                user.stripe_subscription_id = session.get("subscription")
                await db.commit()

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        sub_id = subscription.get("id")
        result = await db.execute(select(User).where(User.stripe_subscription_id == sub_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_pro = False
            user.stripe_subscription_id = None
            await db.commit()

    return {"status": "ok"}
