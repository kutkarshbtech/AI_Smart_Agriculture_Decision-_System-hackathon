"""
Dashboard endpoints.
Aggregated view for farmer decision-making.
"""
from fastapi import APIRouter
from datetime import date

from app.api.routes.produce import _batches
from app.services.pricing_service import pricing_service
from app.services.spoilage_service import spoilage_service
from app.services.alert_service import alert_service

router = APIRouter()


@router.get("/summary/{farmer_id}")
async def get_dashboard_summary(farmer_id: int = 1):
    """
    Get a complete dashboard summary for a farmer.
    Includes batch stats, risk assessment, and top recommendation.
    """
    farmer_batches = [b for b in _batches.values() if b["farmer_id"] == farmer_id]
    active = [b for b in farmer_batches if not b["is_sold"]]
    sold = [b for b in farmer_batches if b["is_sold"]]

    total_qty = sum(b["quantity_kg"] for b in active)
    high_risk = [b for b in active if b.get("spoilage_risk") in ("high", "critical")]

    quality_scores = [b["quality_score"] for b in active if b.get("quality_score")]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None

    # Get alerts count
    alerts_data = alert_service.get_user_alerts(farmer_id)

    # Generate top recommendation
    top_rec = None
    if high_risk:
        top_rec = (
            f"⚠️ {len(high_risk)} batch(es) at high spoilage risk. "
            f"Sell {high_risk[0]['crop_name']} ({high_risk[0]['quantity_kg']} kg) immediately."
        )
    elif active:
        top_rec = "✅ All batches are in good condition. Check market prices for the best selling time."

    return {
        "total_batches": len(farmer_batches),
        "active_batches": len(active),
        "sold_batches": len(sold),
        "total_quantity_kg": total_qty,
        "estimated_value": None,  # Would compute from pricing service
        "avg_quality_score": round(avg_quality, 1) if avg_quality else None,
        "high_risk_batches": len(high_risk),
        "pending_alerts": alerts_data["unread_count"],
        "top_recommendation": top_rec,
    }


@router.get("/actions/{farmer_id}")
async def get_recommended_actions(farmer_id: int = 1):
    """
    Get personalized action recommendations for the farmer.
    Three simple actions: what to sell, where, and at what price.
    """
    farmer_batches = [b for b in _batches.values() if b["farmer_id"] == farmer_id and not b["is_sold"]]

    actions = []

    for batch in farmer_batches:
        crop_name = batch["crop_name"]
        spoilage_risk = batch.get("spoilage_risk", "unknown")

        # Get price recommendation
        recommendation = pricing_service.generate_price_recommendation(
            crop_name=crop_name,
            quantity_kg=batch["quantity_kg"],
            quality_grade=batch.get("quality_grade"),
            spoilage_risk=spoilage_risk,
        )

        action = {
            "batch_id": batch["id"],
            "crop_name": crop_name,
            "quantity_kg": batch["quantity_kg"],
            "action": recommendation["action"],
            "recommended_price_range": {
                "min": recommendation["recommended_min_price"],
                "max": recommendation["recommended_max_price"],
            },
            "spoilage_risk": spoilage_risk,
            "reason": recommendation["recommendation_text"],
        }
        actions.append(action)

    # Sort: critical/high risk first
    risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}
    actions.sort(key=lambda x: risk_order.get(x["spoilage_risk"], 5))

    return {
        "farmer_id": farmer_id,
        "actions": actions,
        "total": len(actions),
    }
