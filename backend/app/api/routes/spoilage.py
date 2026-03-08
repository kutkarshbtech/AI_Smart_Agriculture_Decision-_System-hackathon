"""
Spoilage risk assessment endpoints.
"""
from fastapi import APIRouter, HTTPException
from datetime import date

from app.schemas.spoilage import SpoilageAssessmentRequest, SpoilageAssessmentResponse
from app.services.spoilage_service import spoilage_service
from app.services.weather_service import weather_service
from app.api.routes.produce import _batches

router = APIRouter()


@router.post("/assess")
async def assess_spoilage(request: SpoilageAssessmentRequest):
    """Assess spoilage risk for a produce batch."""
    if request.batch_id not in _batches:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch = _batches[request.batch_id]
    crop_name = batch["crop_name"]
    harvest_date = date.fromisoformat(batch["harvest_date"])

    # Use provided values or fall back to batch stored values
    current_temp = request.current_temp or batch.get("storage_temp")
    current_humidity = request.current_humidity or batch.get("storage_humidity")

    # If farmer has location, get weather data for ambient conditions
    weather_context = None
    if not current_temp and batch.get("location_lat"):
        weather = await weather_service.get_current_weather(
            batch["location_lat"], batch["location_lng"]
        )
        current_temp = weather.get("temperature")
        current_humidity = weather.get("humidity")
        weather_context = weather_service.get_spoilage_weather_context(weather, crop_name)

    result = spoilage_service.predict_spoilage(
        crop_name=crop_name,
        harvest_date=harvest_date,
        storage_type=batch.get("storage_type", "ambient"),
        current_temp=current_temp,
        current_humidity=current_humidity,
        transport_hours=request.transport_hours or 0,
    )

    # Update batch with latest spoilage data
    batch["spoilage_risk"] = result["spoilage_risk"]
    batch["spoilage_probability"] = result["spoilage_probability"]
    batch["estimated_shelf_life_days"] = result["estimated_shelf_life_days"]

    response = {
        "batch_id": request.batch_id,
        "crop_name": crop_name,
        **result,
    }

    if weather_context:
        response["weather_context"] = weather_context

    return response


@router.get("/batch/{batch_id}")
async def get_batch_spoilage(batch_id: int):
    """Get current spoilage status of a batch."""
    if batch_id not in _batches:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch = _batches[batch_id]
    crop_name = batch["crop_name"]
    harvest_date = date.fromisoformat(batch["harvest_date"])

    result = spoilage_service.predict_spoilage(
        crop_name=crop_name,
        harvest_date=harvest_date,
        storage_type=batch.get("storage_type", "ambient"),
        current_temp=batch.get("storage_temp"),
        current_humidity=batch.get("storage_humidity"),
    )

    return {
        "batch_id": batch_id,
        "crop_name": crop_name,
        **result,
    }


@router.get("/weather-impact")
async def get_weather_impact(crop_name: str, lat: float, lng: float):
    """Check how current weather affects spoilage for a specific crop."""
    weather = await weather_service.get_current_weather(lat, lng)
    context = weather_service.get_spoilage_weather_context(weather, crop_name)
    return context
