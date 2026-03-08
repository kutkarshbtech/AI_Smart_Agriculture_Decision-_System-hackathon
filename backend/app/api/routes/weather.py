"""
Weather API Routes
Provides weather forecast and agricultural advisories
"""
from fastapi import APIRouter, Query
from typing import Dict, Any, List
from ...services.weather_service import WeatherService

router = APIRouter()
weather_service = WeatherService()


@router.get("/current")
async def get_current_weather(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude")
) -> Dict[str, Any]:
    """Get current weather for location"""
    return await weather_service.get_current_weather(latitude, longitude)


@router.get("/city/{city}")
async def get_weather_by_city(city: str) -> Dict[str, Any]:
    """Get current weather by city name"""
    return await weather_service.get_weather_by_city(city)


@router.get("/forecast")
async def get_weather_forecast(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    days: int = Query(5, ge=1, le=7, description="Number of days (1-7)")
) -> List[Dict[str, Any]]:
    """Get weather forecast for location"""
    return await weather_service.get_weather_forecast(latitude, longitude, days)


@router.get("/forecast/city/{city}")
async def get_forecast_by_city(
    city: str,
    days: int = Query(5, ge=1, le=7, description="Number of days (1-7)")
) -> List[Dict[str, Any]]:
    """Get weather forecast by city name with agricultural advisories"""
    return await weather_service.get_weather_forecast(city=city)
