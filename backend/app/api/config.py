from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("")
async def get_public_config():
    """Return publicly safe site configuration for the frontend."""
    return {
        "site_name": settings.SITE_NAME,
        "free_daily_summarize_limit": settings.FREE_DAILY_SUMMARIZE_LIMIT,
        "free_max_resolution": settings.FREE_MAX_RESOLUTION,
        "pro_monthly_price": settings.PRO_MONTHLY_PRICE_DISPLAY,
        "pro_monthly_period": "/month",
        "pro_yearly_price": settings.PRO_YEARLY_PRICE_DISPLAY,
        "pro_yearly_period": "/year",
        "pro_yearly_savings": settings.PRO_YEARLY_SAVINGS_DISPLAY,
        "payment_enabled": bool(settings.STRIPE_SECRET_KEY),
    }
