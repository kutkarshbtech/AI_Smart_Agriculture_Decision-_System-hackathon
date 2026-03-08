"""
Logistics API Routes
Provides transport vehicle recommendation and logistics provider matching
"""
from fastapi import APIRouter, Query
from typing import Dict, Any
from ...services.logistics_service import logistics_service

router = APIRouter()


@router.get("/recommend")
async def recommend_vehicle(
    distance_km: float = Query(..., gt=0, description="Distance in km"),
    quantity_kg: float = Query(..., gt=0, description="Quantity in kg"),
    crop_name: str = Query("tomato", description="Crop name"),
    urgency: str = Query("medium", description="Urgency: low, medium, high"),
) -> Dict[str, Any]:
    """Recommend optimal vehicle for transport"""
    try:
        result = logistics_service.recommend_vehicle(
            distance_km=distance_km,
            quantity_kg=quantity_kg,
            crop_name=crop_name,
            urgency=urgency,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/providers")
async def find_providers(
    vehicle_type: str = Query("mini_truck", description="Vehicle type ID"),
    source_state: str = Query("Maharashtra", description="Source state"),
    destination_state: str = Query("Karnataka", description="Destination state"),
    min_rating: float = Query(3.5, ge=1, le=5, description="Minimum provider rating"),
) -> Dict[str, Any]:
    """Find logistics providers for a vehicle type and route"""
    try:
        providers = logistics_service.find_logistics_providers(
            vehicle_type=vehicle_type,
            source_state=source_state,
            destination_state=destination_state,
            min_rating=min_rating,
        )
        return {"success": True, "providers": providers, "total": len(providers)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/complete")
async def complete_recommendation(
    seller_location: str = Query(..., description="Seller location (e.g. 'Pune, Maharashtra')"),
    buyer_location: str = Query(..., description="Buyer location (e.g. 'Mumbai, Maharashtra')"),
    distance_km: float = Query(..., gt=0, description="Distance in km"),
    quantity_kg: float = Query(..., gt=0, description="Quantity in kg"),
    crop_name: str = Query("tomato", description="Crop name"),
    urgency: str = Query("medium", description="Urgency: low, medium, high"),
) -> Dict[str, Any]:
    """Complete logistics recommendation with vehicle, providers, and cost breakdown"""
    try:
        result = logistics_service.get_complete_logistics_recommendation(
            seller_location=seller_location,
            buyer_location=buyer_location,
            distance_km=distance_km,
            quantity_kg=quantity_kg,
            crop_name=crop_name,
            urgency=urgency,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}
