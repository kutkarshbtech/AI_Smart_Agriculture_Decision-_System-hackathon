"""
Alerts endpoints.
Manage farmer notifications for spoilage, price, and buyer events.
"""
from fastapi import APIRouter
from app.services.alert_service import alert_service

router = APIRouter()


@router.get("/user/{user_id}")
async def get_user_alerts(user_id: int, unread_only: bool = False):
    """Get all alerts for a user."""
    return alert_service.get_user_alerts(user_id, unread_only)


@router.post("/{alert_id}/read")
async def mark_alert_read(alert_id: int):
    """Mark an alert as read."""
    success = alert_service.mark_as_read(alert_id)
    if not success:
        return {"status": "not_found"}
    return {"status": "ok"}


@router.post("/test/spoilage")
async def create_test_spoilage_alert(
    user_id: int = 1,
    crop_name: str = "Tomato",
    risk_level: str = "high",
    remaining_days: int = 2,
    batch_id: int = 1,
):
    """Create a test spoilage alert (for demo purposes)."""
    alert = alert_service.create_spoilage_alert(
        user_id=user_id,
        crop_name=crop_name,
        risk_level=risk_level,
        remaining_days=remaining_days,
        batch_id=batch_id,
    )
    return alert


@router.post("/test/price")
async def create_test_price_alert(
    user_id: int = 1,
    crop_name: str = "Onion",
    trend: str = "falling",
    current_price: float = 18.5,
    change_pct: float = -8.5,
):
    """Create a test price alert (for demo purposes)."""
    alert = alert_service.create_price_alert(
        user_id=user_id,
        crop_name=crop_name,
        trend=trend,
        current_price=current_price,
        change_pct=change_pct,
    )
    return alert
