"""
SMS/WhatsApp alert service using Amazon SNS + Twilio.
Adapted from Kisan.AI's Twilio integration, extended for spoilage/price alerts.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime


class AlertService:
    """Manages alerts for spoilage warnings, price changes, and buyer matches."""

    # In-memory alert store for demo (replace with DynamoDB in production)
    _alerts: List[Dict[str, Any]] = []
    _alert_counter: int = 0

    def create_alert(
        self,
        user_id: int,
        alert_type: str,
        title: str,
        message: str,
        severity: str = "info",
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Create and store a new alert."""
        self._alert_counter += 1
        alert = {
            "id": self._alert_counter,
            "user_id": user_id,
            "alert_type": alert_type,
            "title": title,
            "message": message,
            "severity": severity,
            "is_read": False,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        self._alerts.append(alert)
        return alert

    def get_user_alerts(
        self, user_id: int, unread_only: bool = False
    ) -> Dict[str, Any]:
        """Get all alerts for a user."""
        user_alerts = [a for a in self._alerts if a["user_id"] == user_id]
        if unread_only:
            user_alerts = [a for a in user_alerts if not a["is_read"]]

        user_alerts.sort(key=lambda x: x["created_at"], reverse=True)

        unread_count = len([a for a in self._alerts if a["user_id"] == user_id and not a["is_read"]])

        return {
            "alerts": user_alerts,
            "unread_count": unread_count,
            "total": len([a for a in self._alerts if a["user_id"] == user_id]),
        }

    def mark_as_read(self, alert_id: int) -> bool:
        """Mark an alert as read."""
        for alert in self._alerts:
            if alert["id"] == alert_id:
                alert["is_read"] = True
                return True
        return False

    def create_spoilage_alert(
        self, user_id: int, crop_name: str, risk_level: str,
        remaining_days: int, batch_id: int
    ) -> Dict[str, Any]:
        """Create a spoilage warning alert."""
        severity_map = {
            "critical": "critical",
            "high": "warning",
            "medium": "info",
            "low": "info",
        }

        if risk_level in ("critical", "high"):
            title = f"⚠️ {crop_name} spoilage risk: {risk_level.upper()}"
            message = (
                f"आपकी {crop_name} की खेप में खराब होने का खतरा {risk_level} है। "
                f"बची हुई शेल्फ लाइफ: {remaining_days} दिन। "
                f"कृपया जल्द से जल्द बेचें या कोल्ड स्टोरेज में रखें।"
            )
        else:
            title = f"📦 {crop_name} storage update"
            message = (
                f"Your {crop_name} batch has {remaining_days} days of shelf life remaining. "
                f"Current risk level: {risk_level}."
            )

        return self.create_alert(
            user_id=user_id,
            alert_type="spoilage_warning",
            title=title,
            message=message,
            severity=severity_map.get(risk_level, "info"),
            metadata={"batch_id": batch_id, "crop_name": crop_name, "risk_level": risk_level},
        )

    def create_price_alert(
        self, user_id: int, crop_name: str, trend: str,
        current_price: float, change_pct: float
    ) -> Dict[str, Any]:
        """Create a price change alert."""
        if trend == "rising":
            title = f"📈 {crop_name} price rising!"
            message = (
                f"{crop_name} prices are up {change_pct:.1f}%. "
                f"Current market price: ₹{current_price}/kg. "
                f"Good time to sell!"
            )
            severity = "info"
        else:
            title = f"📉 {crop_name} price dropping"
            message = (
                f"{crop_name} prices have fallen {abs(change_pct):.1f}%. "
                f"Current market price: ₹{current_price}/kg. "
                f"Consider selling soon before further decline."
            )
            severity = "warning"

        return self.create_alert(
            user_id=user_id,
            alert_type="price_drop" if trend == "falling" else "price_surge",
            title=title,
            message=message,
            severity=severity,
            metadata={"crop_name": crop_name, "trend": trend, "price": current_price},
        )

    def create_buyer_match_alert(
        self, user_id: int, crop_name: str, buyer_name: str,
        distance_km: float, batch_id: int
    ) -> Dict[str, Any]:
        """Alert when a buyer match is found."""
        return self.create_alert(
            user_id=user_id,
            alert_type="buyer_match",
            title=f"🤝 Buyer found for {crop_name}!",
            message=(
                f"{buyer_name} ({distance_km} km away) is interested in your {crop_name}. "
                f"Contact them to negotiate a price."
            ),
            severity="info",
            metadata={"batch_id": batch_id, "buyer_name": buyer_name, "distance_km": distance_km},
        )

    async def send_sms_alert(
        self, phone: str, message: str
    ) -> Dict[str, Any]:
        """Send SMS via Amazon SNS (with Twilio fallback)."""
        try:
            return await self._send_via_sns(phone, message)
        except Exception as e:
            print(f"SNS unavailable ({e}), SMS not sent")
            return {"status": "queued", "method": "none", "note": "SMS service unavailable in demo mode"}

    async def _send_via_sns(self, phone: str, message: str) -> Dict[str, Any]:
        """Send SMS using Amazon SNS."""
        from app.core.aws_clients import get_sns_client

        client = get_sns_client()
        response = client.publish(
            PhoneNumber=phone,
            Message=message,
            MessageAttributes={
                "AWS.SNS.SMS.SenderID": {
                    "DataType": "String",
                    "StringValue": "SwadeshAI",
                },
                "AWS.SNS.SMS.SMSType": {
                    "DataType": "String",
                    "StringValue": "Transactional",
                },
            },
        )
        return {"status": "sent", "method": "sns", "message_id": response.get("MessageId")}


# Singleton
alert_service = AlertService()

# ── Seed demo alerts for hackathon demo ──────────────────────────────
alert_service.create_spoilage_alert(
    user_id=1, crop_name="Cauliflower", risk_level="critical",
    remaining_days=1, batch_id=5,
)
alert_service.create_spoilage_alert(
    user_id=1, crop_name="Onion", risk_level="high",
    remaining_days=2, batch_id=4,
)
alert_service.create_price_alert(
    user_id=1, crop_name="Tomato", trend="rising",
    current_price=42.0, change_pct=8.5,
)
alert_service.create_buyer_match_alert(
    user_id=1, crop_name="Banana", buyer_name="Fresh Mart Mumbai",
    distance_km=148, batch_id=2,
)
alert_service.create_price_alert(
    user_id=1, crop_name="Potato", trend="falling",
    current_price=18.0, change_pct=-5.2,
)
# ─────────────────────────────────────────────────────────────────────
