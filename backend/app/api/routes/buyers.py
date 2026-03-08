"""
Buyer matching endpoints.
Find nearby buyers, view active demands, create offers, and manage negotiations.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from app.schemas.buyer_alert import (
    BuyerMatchRequest,
    BuyerMatchResponse,
    OfferCreateRequest,
    OfferResponse,
    OfferUpdateRequest,
    ActiveDemandResponse,
)
from app.services.buyer_service import buyer_service
from app.api.routes.produce import _batches

router = APIRouter()


# ─── Matching ────────────────────────────────────────────────────────────

@router.post("/match")
async def find_matching_buyers(request: BuyerMatchRequest):
    """
    Find and rank buyers for a produce batch using multi-factor scoring.

    Scores are based on distance, rating, capacity fit, payment speed,
    active demand urgency, and reliability. Returns sorted by composite score.
    """
    if request.batch_id not in _batches:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch = _batches[request.batch_id]
    crop_name = batch["crop_name"]

    matches = buyer_service.find_matching_buyers(
        crop_name=crop_name,
        farmer_lat=request.farmer_lat,
        farmer_lng=request.farmer_lng,
        quantity_kg=batch["quantity_kg"],
        max_distance_km=request.max_distance_km,
        buyer_type=request.buyer_type,
        min_rating=request.min_rating,
        sort_by=request.sort_by or "score",
    )

    return {
        "batch_id": request.batch_id,
        "crop_name": crop_name,
        "matched_buyers": matches,
        "total_matches": len(matches),
    }


@router.get("/nearby")
async def find_nearby_buyers(
    crop_name: str,
    lat: float,
    lng: float,
    quantity_kg: float = 100,
    max_distance_km: float = 100,
    buyer_type: Optional[str] = None,
    min_rating: Optional[float] = None,
    sort_by: str = "score",
):
    """
    Find and rank buyers near a location for a specific crop (no batch required).

    Supports filtering by buyer_type (retailer, wholesaler, aggregator)
    and minimum rating. Sort by 'score', 'distance', or 'rating'.
    """
    matches = buyer_service.find_matching_buyers(
        crop_name=crop_name,
        farmer_lat=lat,
        farmer_lng=lng,
        quantity_kg=quantity_kg,
        max_distance_km=max_distance_km,
        buyer_type=buyer_type,
        min_rating=min_rating,
        sort_by=sort_by,
    )

    return {
        "crop_name": crop_name,
        "search_location": {"lat": lat, "lng": lng},
        "max_distance_km": max_distance_km,
        "matched_buyers": matches,
        "total_matches": len(matches),
    }


# ─── Active Demands ─────────────────────────────────────────────────────

@router.get("/demands")
async def get_active_demands(
    crop_name: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    max_distance_km: float = 100,
):
    """
    Get active buyer demand requests.

    Shows what buyers are currently looking for, with urgency levels.
    Filter by crop name and/or farmer location.
    """
    demands = buyer_service.get_active_demands(
        crop_name=crop_name,
        farmer_lat=lat,
        farmer_lng=lng,
        max_distance_km=max_distance_km,
    )

    return {
        "demands": demands,
        "total": len(demands),
    }


# ─── Offers / Negotiation ───────────────────────────────────────────────

@router.post("/offers")
async def create_offer(request: OfferCreateRequest):
    """
    Send a sell offer from a farmer to a buyer.

    The buyer can accept, counter-offer, or reject within 24 hours.
    """
    buyer = buyer_service.get_buyer_by_id(request.buyer_id)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    if request.batch_id and request.batch_id not in _batches:
        raise HTTPException(status_code=404, detail="Batch not found")

    offer = buyer_service.create_offer(
        farmer_id=request.farmer_id,
        buyer_id=request.buyer_id,
        crop_name=request.crop_name,
        quantity_kg=request.quantity_kg,
        asking_price_per_kg=request.asking_price_per_kg,
        batch_id=request.batch_id,
        notes=request.notes,
    )

    if "error" in offer:
        raise HTTPException(status_code=400, detail=offer["error"])

    return offer


@router.get("/offers/{offer_id}")
async def get_offer(offer_id: int):
    """Get details of a specific offer."""
    offer = buyer_service.get_offer(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer


@router.put("/offers/{offer_id}")
async def update_offer(offer_id: int, request: OfferUpdateRequest):
    """
    Update an offer status: accept, reject, or counter-offer.

    For counter-offers, include counter_price_per_kg.
    """
    offer = buyer_service.get_offer(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    if offer["status"] != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update offer with status '{offer['status']}'"
        )

    updated = buyer_service.update_offer_status(
        offer_id=offer_id,
        status=request.status,
        counter_price=request.counter_price_per_kg,
    )
    if not updated:
        raise HTTPException(status_code=400, detail="Invalid update")

    return updated


@router.get("/offers")
async def list_farmer_offers(
    farmer_id: int = 1,
    status: Optional[str] = None,
):
    """List all offers for a farmer, optionally filtered by status."""
    offers = buyer_service.get_farmer_offers(farmer_id, status=status)
    return {
        "offers": offers,
        "total": len(offers),
    }


# ─── Buyer Details ───────────────────────────────────────────────────────

@router.get("/list")
async def list_all_buyers(
    buyer_type: Optional[str] = None,
    state: Optional[str] = None,
):
    """List all registered buyers with optional filters."""
    buyers = buyer_service.get_all_buyers(buyer_type=buyer_type, state=state)
    return {
        "buyers": buyers,
        "total": len(buyers),
    }


@router.get("/{buyer_id}")
async def get_buyer_details(buyer_id: int):
    """Get details of a specific buyer."""
    buyer = buyer_service.get_buyer_by_id(buyer_id)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return buyer
