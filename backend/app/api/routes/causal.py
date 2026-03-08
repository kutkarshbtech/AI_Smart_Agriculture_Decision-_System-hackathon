"""
Causal Inference API Routes
Provides causal analysis for agricultural decisions using DoWhy
"""
from fastapi import APIRouter, Query
from typing import Dict, Any
from ...services.causal_service import causal_service

router = APIRouter()


@router.get("/storage-spoilage")
async def analyze_storage_effect(
    crop_name: str = Query("tomato", description="Crop name"),
    quality_grade: str = Query("good", description="Quality grade"),
) -> Dict[str, Any]:
    """Analyze causal effect of cold storage on spoilage rates"""
    try:
        result = causal_service.analyze_storage_effect_on_spoilage(
            crop_name=crop_name,
            quality_grade=quality_grade,
        )
        return {
            "success": True,
            "analysis": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Causal analysis failed. Using fallback data."
        }


@router.get("/weather-prices")
async def analyze_weather_effect(
    crop_name: str = Query("tomato", description="Crop name"),
    location: str = Query("Lucknow", description="Location"),
) -> Dict[str, Any]:
    """Analyze causal effect of weather on market prices"""
    try:
        result = causal_service.analyze_weather_effect_on_prices(
            crop_name=crop_name,
            location=location,
        )
        return {
            "success": True,
            "analysis": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Causal analysis failed. Using fallback data."
        }


@router.get("/quality-premium")
async def analyze_quality_effect(
    crop_name: str = Query("tomato", description="Crop name"),
) -> Dict[str, Any]:
    """Analyze causal effect of quality on price premium"""
    try:
        result = causal_service.analyze_quality_effect_on_price(
            crop_name=crop_name,
        )
        return {
            "success": True,
            "analysis": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Causal analysis failed. Using fallback data."
        }
