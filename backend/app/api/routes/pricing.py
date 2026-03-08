"""
Pricing intelligence endpoints.
Market prices, AI-powered price recommendations, forecasts, what-if analysis,
and live mandi prices from data.gov.in.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import date as date_type, datetime, timedelta, timezone

from app.schemas.pricing import (
    PriceRecommendationResponse,
    PriceTrendResponse,
    PriceForecastResponse,
    PriceRecommendationRequest,
    WhatIfRequest,
    WhatIfResponse,
    MandiPriceListResponse,
    MandiPriceSummary,
)
from app.services.pricing_service import pricing_service
from app.services.mandi_service import mandi_client
from app.api.routes.produce import _batches, CROP_NAME_MAP

router = APIRouter()


@router.get("/market/{crop_name}")
async def get_market_prices(crop_name: str, days: int = 7):
    """Get recent market prices for a crop."""
    prices = pricing_service.get_daily_prices(crop_name, days=days)
    trend = pricing_service.get_price_trend(crop_name)
    modal_prices = [p["modal_price"] for p in prices]
    avg_7d = sum(modal_prices) / len(modal_prices) if modal_prices else 0

    return {
        "crop_name": crop_name,
        "mandi_name": prices[-1]["mandi_name"] if prices else "N/A",
        "prices": prices,
        "trend": trend,
        "avg_price_7d": round(avg_7d, 2),
        "avg_price_30d": None,  # Would require 30-day fetch
    }


@router.get("/recommend/{batch_id}")
async def get_price_recommendation(batch_id: int):
    """
    Get AI-powered price recommendation for a produce batch.

    Returns ideal price range, seller-protected floor, confidence score,
    explainable factors, 3-day forecast, and what-if scenarios.
    """
    if batch_id not in _batches:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch = _batches[batch_id]
    crop_name = batch["crop_name"]

    # Parse harvest_date
    harvest_date = batch.get("harvest_date")
    if isinstance(harvest_date, str):
        harvest_date = date_type.fromisoformat(harvest_date)

    recommendation = pricing_service.generate_price_recommendation(
        crop_name=crop_name,
        quantity_kg=batch["quantity_kg"],
        quality_grade=batch.get("quality_grade"),
        spoilage_risk=batch.get("spoilage_risk"),
        remaining_shelf_life_days=batch.get("estimated_shelf_life_days"),
        spoilage_probability=batch.get("spoilage_probability"),
        harvest_date=harvest_date,
        storage_type=batch.get("storage_type", "ambient"),
        storage_temp=batch.get("storage_temp"),
        storage_humidity=batch.get("storage_humidity"),
        farmer_lat=batch.get("location_lat"),
        farmer_lng=batch.get("location_lng"),
    )

    return {
        "batch_id": batch_id,
        "crop_name": crop_name,
        "quantity_kg": batch["quantity_kg"],
        **recommendation,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/recommend")
async def get_price_recommendation_direct(request: PriceRecommendationRequest):
    """
    Get price recommendation without a batch — provide crop details directly.

    Useful for quick price checks before registering a batch.
    """
    recommendation = pricing_service.generate_price_recommendation(
        crop_name=request.crop_name,
        quantity_kg=request.quantity_kg,
        quality_grade=request.quality_grade,
        spoilage_risk=request.spoilage_risk,
        remaining_shelf_life_days=request.remaining_shelf_life_days,
        harvest_date=request.harvest_date,
        storage_type=request.storage_type or "ambient",
        storage_temp=request.storage_temp,
        storage_humidity=request.storage_humidity,
        farmer_lat=request.farmer_location_lat,
        farmer_lng=request.farmer_location_lng,
    )

    return {
        "crop_name": request.crop_name,
        "quantity_kg": request.quantity_kg,
        **recommendation,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/forecast/{crop_name}")
async def get_price_forecast(crop_name: str, days_ahead: int = 3):
    """
    Get price forecast for the next N days (max 7).

    Uses trend extrapolation from recent market data.
    """
    if days_ahead < 1 or days_ahead > 7:
        raise HTTPException(status_code=400, detail="days_ahead must be 1-7")

    forecast = pricing_service.forecast_prices(crop_name, days_ahead=days_ahead)
    trend = pricing_service.get_price_trend(crop_name)

    return {
        "crop_name": crop_name,
        "current_trend": trend,
        "forecast": forecast,
    }


@router.get("/weather-forecast/{crop_name}")
async def get_weather_price_forecast(
    crop_name: str,
    days_ahead: int = 5,
    city: Optional[str] = None,
    quality_grade: Optional[str] = None,
    storage_type: str = "ambient",
    harvest_days_ago: int = 1,
):
    """
    Weather-aware price & crop health forecast.

    Uses OpenWeatherMap 5-day forecast to predict how upcoming weather
    conditions (temperature, humidity, rainfall) affect:
    - Crop health & remaining shelf life
    - Spoilage acceleration rate
    - Market supply disruptions → price impact

    Returns daily forecast with crop health scores, projected prices,
    weather risk levels, and an overall sell/wait/store recommendation.

    Examples:
        GET /api/v1/pricing/weather-forecast/tomato?city=Delhi
        GET /api/v1/pricing/weather-forecast/banana?city=Mumbai&quality_grade=good&storage_type=cold
    """
    if days_ahead < 1 or days_ahead > 5:
        raise HTTPException(status_code=400, detail="days_ahead must be 1-5")

    harvest_date = date_type.today() - timedelta(days=harvest_days_ago)

    result = await pricing_service.forecast_prices_weather(
        crop_name=crop_name,
        days_ahead=days_ahead,
        city=city or "Delhi",
        quality_grade=quality_grade,
        storage_type=storage_type,
        harvest_date=harvest_date,
    )

    return result


@router.get("/trends/{crop_name}")
async def get_price_trends(crop_name: str):
    """Get price trend analysis for a crop."""
    prices = pricing_service.get_daily_prices(crop_name, days=14)
    trend = pricing_service.get_price_trend(crop_name)
    modal_prices = [p["modal_price"] for p in prices]

    avg_7d = sum(modal_prices[-7:]) / min(7, len(modal_prices)) if modal_prices else 0
    avg_14d = sum(modal_prices) / len(modal_prices) if modal_prices else 0

    return {
        "crop_name": crop_name,
        "trend": trend,
        "avg_price_7d": round(avg_7d, 2),
        "avg_price_14d": round(avg_14d, 2),
        "latest_price": modal_prices[-1] if modal_prices else None,
        "price_history": prices,
    }


@router.get("/feature-importance")
async def get_feature_importance():
    """
    Get the ML model's feature importances.

    Useful for explaining which factors most affect price predictions.
    """
    importance = pricing_service.get_feature_importance()
    return {
        "feature_importances": importance,
        "model_type": "xgboost" if importance else "rule_based",
    }


# ═══════════════════════════════════════════════════════════
#   Live Mandi Prices  (data.gov.in)
# ═══════════════════════════════════════════════════════════


@router.get("/mandi/prices/{commodity}")
async def get_mandi_prices(
    commodity: str,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    limit: int = 30,
):
    """
    Fetch live daily mandi prices for a commodity from data.gov.in.

    Prices are returned in both ₹/quintal (original) and ₹/kg (normalised).

    Examples:
        GET /api/v1/pricing/mandi/prices/tomato
        GET /api/v1/pricing/mandi/prices/onion?state=Maharashtra
        GET /api/v1/pricing/mandi/prices/potato?state=Uttar Pradesh&market=Agra
    """
    result = await mandi_client.fetch_prices(
        commodity, state=state, district=district, market=market, limit=limit,
    )

    if result.get("api_error") and not result["records"]:
        raise HTTPException(
            status_code=502,
            detail=f"Mandi API error: {result['api_error']}. "
                   "Check that MANDI_API_KEY is configured in .env",
        )

    return result


@router.get("/mandi/summary/{commodity}")
async def get_mandi_summary(
    commodity: str,
    state: Optional[str] = None,
):
    """
    Get an aggregated price summary for a commodity across mandis.

    Returns avg, min, max, median price in ₹/kg and the list of
    reporting states.

    Examples:
        GET /api/v1/pricing/mandi/summary/tomato
        GET /api/v1/pricing/mandi/summary/onion?state=Maharashtra
    """
    summary = await mandi_client.get_commodity_summary(commodity, state=state)

    if summary["num_mandis"] == 0 and summary.get("api_error"):
        raise HTTPException(
            status_code=502,
            detail=f"Mandi API error: {summary['api_error']}",
        )

    return summary


@router.get("/mandi/compare/{commodity}")
async def compare_mandi_prices(
    commodity: str,
    states: Optional[str] = None,
    limit_per_state: int = 10,
):
    """
    Compare mandi prices for a commodity across multiple states.

    Pass states as comma-separated: ?states=Maharashtra,Karnataka,Delhi

    Returns per-state statistics for easy comparison.
    """
    state_list = [s.strip() for s in states.split(",")] if states else None

    records = await mandi_client.fetch_prices_multi_market(
        commodity, states=state_list, limit_per_state=limit_per_state,
    )

    if not records:
        return {
            "commodity": commodity,
            "states_compared": state_list or [],
            "state_summaries": [],
            "best_market": None,
        }

    # Group by state
    state_groups: dict = {}
    for r in records:
        st = r.get("state", "Unknown")
        state_groups.setdefault(st, []).append(r)

    summaries = []
    for st, recs in sorted(state_groups.items()):
        modals = [r["modal_price_per_kg"] for r in recs]
        summaries.append({
            "state": st,
            "num_mandis": len(recs),
            "avg_price_per_kg": round(sum(modals) / len(modals), 2),
            "min_price_per_kg": round(min(modals), 2),
            "max_price_per_kg": round(max(modals), 2),
            "markets": [
                {"market": r.get("market"), "modal_price_per_kg": r["modal_price_per_kg"]}
                for r in sorted(recs, key=lambda x: -x["modal_price_per_kg"])[:5]
            ],
        })

    # Best market overall
    best = max(records, key=lambda r: r["modal_price_per_kg"])

    return {
        "commodity": commodity,
        "states_compared": list(state_groups.keys()),
        "state_summaries": summaries,
        "best_market": {
            "market": best.get("market"),
            "state": best.get("state"),
            "modal_price_per_kg": best["modal_price_per_kg"],
        },
    }
