"""
Produce management endpoints.
CRUD for crop batches, image upload, and batch listing.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from datetime import date, datetime, timezone

from app.schemas.produce import (
    ProduceBatchCreate, ProduceBatchResponse, ProduceBatchUpdate, CropTypeResponse
)
from app.services.quality_service import quality_service
from app.services.spoilage_service import spoilage_service

router = APIRouter()

# In-memory storage for hackathon demo
_batches: dict = {}
_batch_counter = 0

# Supported crop types
CROP_TYPES = [
    {"id": 1, "name_en": "Tomato", "name_hi": "टमाटर", "category": "vegetable", "avg_shelf_life_days": 7, "optimal_temp_min": 10, "optimal_temp_max": 15, "image_url": None},
    {"id": 2, "name_en": "Potato", "name_hi": "आलू", "category": "vegetable", "avg_shelf_life_days": 30, "optimal_temp_min": 4, "optimal_temp_max": 8, "image_url": None},
    {"id": 3, "name_en": "Onion", "name_hi": "प्याज", "category": "vegetable", "avg_shelf_life_days": 30, "optimal_temp_min": 0, "optimal_temp_max": 4, "image_url": None},
    {"id": 4, "name_en": "Banana", "name_hi": "केला", "category": "fruit", "avg_shelf_life_days": 5, "optimal_temp_min": 13, "optimal_temp_max": 15, "image_url": None},
    {"id": 5, "name_en": "Mango", "name_hi": "आम", "category": "fruit", "avg_shelf_life_days": 5, "optimal_temp_min": 10, "optimal_temp_max": 13, "image_url": None},
    {"id": 6, "name_en": "Apple", "name_hi": "सेब", "category": "fruit", "avg_shelf_life_days": 14, "optimal_temp_min": 0, "optimal_temp_max": 4, "image_url": None},
    {"id": 7, "name_en": "Rice", "name_hi": "चावल", "category": "grain", "avg_shelf_life_days": 365, "optimal_temp_min": 15, "optimal_temp_max": 20, "image_url": None},
    {"id": 8, "name_en": "Wheat", "name_hi": "गेहूं", "category": "grain", "avg_shelf_life_days": 180, "optimal_temp_min": 15, "optimal_temp_max": 20, "image_url": None},
    {"id": 9, "name_en": "Cauliflower", "name_hi": "फूलगोभी", "category": "vegetable", "avg_shelf_life_days": 4, "optimal_temp_min": 0, "optimal_temp_max": 2, "image_url": None},
    {"id": 10, "name_en": "Spinach", "name_hi": "पालक", "category": "vegetable", "avg_shelf_life_days": 2, "optimal_temp_min": 0, "optimal_temp_max": 2, "image_url": None},
    {"id": 11, "name_en": "Capsicum", "name_hi": "शिमला मिर्च", "category": "vegetable", "avg_shelf_life_days": 5, "optimal_temp_min": 7, "optimal_temp_max": 10, "image_url": None},
    {"id": 12, "name_en": "Okra", "name_hi": "भिंडी", "category": "vegetable", "avg_shelf_life_days": 3, "optimal_temp_min": 7, "optimal_temp_max": 10, "image_url": None},
    {"id": 13, "name_en": "Brinjal", "name_hi": "बैंगन", "category": "vegetable", "avg_shelf_life_days": 5, "optimal_temp_min": 10, "optimal_temp_max": 12, "image_url": None},
    {"id": 14, "name_en": "Guava", "name_hi": "अमरूद", "category": "fruit", "avg_shelf_life_days": 5, "optimal_temp_min": 8, "optimal_temp_max": 10, "image_url": None},
    {"id": 15, "name_en": "Grape", "name_hi": "अंगूर", "category": "fruit", "avg_shelf_life_days": 3, "optimal_temp_min": -1, "optimal_temp_max": 0, "image_url": None},
    {"id": 16, "name_en": "Carrot", "name_hi": "गाजर", "category": "vegetable", "avg_shelf_life_days": 7, "optimal_temp_min": 0, "optimal_temp_max": 2, "image_url": None},
]

CROP_NAME_MAP = {c["id"]: c["name_en"] for c in CROP_TYPES}


# ── Seed demo batches so dashboard is populated on startup ────────────
def _seed_demo_batches():
    """Pre-populate a handful of realistic batches for demo / hackathon."""
    global _batch_counter

    today = date.today()
    demo_entries = [
        # farmer_id 1 – small Pune farmer
        {
            "farmer_id": 1,
            "crop_type_id": 1,
            "crop_name": "Tomato",
            "quantity_kg": 250,
            "harvest_date": (today - __import__("datetime").timedelta(days=2)).isoformat(),
            "storage_type": "ambient",
            "storage_temp": 28,
            "storage_humidity": 65,
            "location_lat": 18.52,
            "location_lng": 73.86,
            "quality_grade": "good",
            "quality_score": 72,
            "spoilage_risk": "medium",
            "spoilage_probability": 0.35,
            "estimated_shelf_life_days": 4,
            "is_sold": False,
            "notes": "Farm harvest – Pune",
        },
        {
            "farmer_id": 1,
            "crop_type_id": 4,
            "crop_name": "Banana",
            "quantity_kg": 500,
            "harvest_date": (today - __import__("datetime").timedelta(days=1)).isoformat(),
            "storage_type": "cold_storage",
            "storage_temp": 14,
            "storage_humidity": 85,
            "location_lat": 18.52,
            "location_lng": 73.86,
            "quality_grade": "excellent",
            "quality_score": 88,
            "spoilage_risk": "low",
            "spoilage_probability": 0.10,
            "estimated_shelf_life_days": 6,
            "is_sold": False,
            "notes": "Cold stored bananas",
        },
        {
            "farmer_id": 1,
            "crop_type_id": 2,
            "crop_name": "Potato",
            "quantity_kg": 1000,
            "harvest_date": (today - __import__("datetime").timedelta(days=10)).isoformat(),
            "storage_type": "cold_storage",
            "storage_temp": 6,
            "storage_humidity": 90,
            "location_lat": 18.52,
            "location_lng": 73.86,
            "quality_grade": "good",
            "quality_score": 78,
            "spoilage_risk": "low",
            "spoilage_probability": 0.08,
            "estimated_shelf_life_days": 25,
            "is_sold": False,
            "notes": "Large potato batch",
        },
        {
            "farmer_id": 1,
            "crop_type_id": 3,
            "crop_name": "Onion",
            "quantity_kg": 300,
            "harvest_date": (today - __import__("datetime").timedelta(days=5)).isoformat(),
            "storage_type": "ambient",
            "storage_temp": 30,
            "storage_humidity": 70,
            "location_lat": 18.52,
            "location_lng": 73.86,
            "quality_grade": "average",
            "quality_score": 55,
            "spoilage_risk": "high",
            "spoilage_probability": 0.62,
            "estimated_shelf_life_days": 2,
            "is_sold": False,
            "notes": "Ambient stored – needs selling",
        },
        {
            "farmer_id": 1,
            "crop_type_id": 9,
            "crop_name": "Cauliflower",
            "quantity_kg": 80,
            "harvest_date": (today - __import__("datetime").timedelta(days=3)).isoformat(),
            "storage_type": "ambient",
            "storage_temp": 25,
            "storage_humidity": 60,
            "location_lat": 18.52,
            "location_lng": 73.86,
            "quality_grade": "poor",
            "quality_score": 38,
            "spoilage_risk": "critical",
            "spoilage_probability": 0.85,
            "estimated_shelf_life_days": 1,
            "is_sold": False,
            "notes": "Wilting – sell urgently",
        },
        # Already sold batch for farmer 1
        {
            "farmer_id": 1,
            "crop_type_id": 1,
            "crop_name": "Tomato",
            "quantity_kg": 150,
            "harvest_date": (today - __import__("datetime").timedelta(days=7)).isoformat(),
            "storage_type": "ambient",
            "storage_temp": 26,
            "storage_humidity": 60,
            "location_lat": 18.52,
            "location_lng": 73.86,
            "quality_grade": "good",
            "quality_score": 70,
            "spoilage_risk": "low",
            "spoilage_probability": 0.05,
            "estimated_shelf_life_days": 0,
            "is_sold": True,
            "notes": "Sold to Mumbai retailer",
        },
        # farmer_id 2 – another demo farmer
        {
            "farmer_id": 2,
            "crop_type_id": 5,
            "crop_name": "Mango",
            "quantity_kg": 400,
            "harvest_date": (today - __import__("datetime").timedelta(days=1)).isoformat(),
            "storage_type": "cold_storage",
            "storage_temp": 12,
            "storage_humidity": 85,
            "location_lat": 19.08,
            "location_lng": 72.88,
            "quality_grade": "excellent",
            "quality_score": 92,
            "spoilage_risk": "low",
            "spoilage_probability": 0.07,
            "estimated_shelf_life_days": 5,
            "is_sold": False,
            "notes": "Alphonso mangoes – Mumbai",
        },
        {
            "farmer_id": 2,
            "crop_type_id": 11,
            "crop_name": "Capsicum",
            "quantity_kg": 120,
            "harvest_date": (today - __import__("datetime").timedelta(days=4)).isoformat(),
            "storage_type": "ambient",
            "storage_temp": 32,
            "storage_humidity": 55,
            "location_lat": 19.08,
            "location_lng": 72.88,
            "quality_grade": "average",
            "quality_score": 52,
            "spoilage_risk": "high",
            "spoilage_probability": 0.58,
            "estimated_shelf_life_days": 2,
            "is_sold": False,
            "notes": "Needs quick sale",
        },
    ]

    for entry in demo_entries:
        _batch_counter += 1
        batch_data = {
            "id": _batch_counter,
            "image_urls": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            **entry,
        }
        _batches[_batch_counter] = batch_data


_seed_demo_batches()

# ──────────────────────────────────────────────────────────────────────


@router.get("/crop-types", response_model=List[CropTypeResponse])
async def list_crop_types(category: Optional[str] = None):
    """List all supported crop types, optionally filtered by category."""
    crops = CROP_TYPES
    if category:
        crops = [c for c in crops if c["category"] == category]
    return crops


@router.post("/batches", response_model=ProduceBatchResponse)
async def create_batch(batch: ProduceBatchCreate):
    """Register a new produce batch for a farmer."""
    global _batch_counter

    crop_name = CROP_NAME_MAP.get(batch.crop_type_id)
    if not crop_name:
        raise HTTPException(status_code=400, detail="Invalid crop_type_id")

    _batch_counter += 1
    batch_id = _batch_counter

    # Auto-run spoilage assessment
    spoilage = spoilage_service.predict_spoilage(
        crop_name=crop_name,
        harvest_date=batch.harvest_date,
        storage_type=batch.storage_type,
        current_temp=batch.storage_temp,
        current_humidity=batch.storage_humidity,
    )

    batch_data = {
        "id": batch_id,
        "farmer_id": 1,  # Hardcoded for demo; use auth in production
        "crop_type_id": batch.crop_type_id,
        "crop_name": crop_name,
        "quantity_kg": batch.quantity_kg,
        "harvest_date": batch.harvest_date.isoformat(),
        "storage_type": batch.storage_type,
        "storage_temp": batch.storage_temp,
        "storage_humidity": batch.storage_humidity,
        "location_lat": batch.location_lat,
        "location_lng": batch.location_lng,
        "image_urls": [],
        "quality_grade": None,
        "quality_score": None,
        "spoilage_risk": spoilage["spoilage_risk"],
        "spoilage_probability": spoilage["spoilage_probability"],
        "estimated_shelf_life_days": spoilage["estimated_shelf_life_days"],
        "is_sold": False,
        "notes": batch.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    _batches[batch_id] = batch_data
    return batch_data


@router.get("/batches", response_model=List[ProduceBatchResponse])
async def list_batches(farmer_id: int = 1, include_sold: bool = False):
    """List all produce batches for a farmer."""
    batches = list(_batches.values())
    batches = [b for b in batches if b["farmer_id"] == farmer_id]
    if not include_sold:
        batches = [b for b in batches if not b["is_sold"]]
    return batches


@router.get("/batches/{batch_id}", response_model=ProduceBatchResponse)
async def get_batch(batch_id: int):
    """Get details of a specific batch."""
    if batch_id not in _batches:
        raise HTTPException(status_code=404, detail="Batch not found")
    return _batches[batch_id]


@router.put("/batches/{batch_id}", response_model=ProduceBatchResponse)
async def update_batch(batch_id: int, update: ProduceBatchUpdate):
    """Update a produce batch."""
    if batch_id not in _batches:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch = _batches[batch_id]
    update_data = update.model_dump(exclude_unset=True)
    batch.update(update_data)

    # Re-run spoilage if storage conditions changed
    if "storage_temp" in update_data or "storage_humidity" in update_data:
        spoilage = spoilage_service.predict_spoilage(
            crop_name=batch["crop_name"],
            harvest_date=date.fromisoformat(batch["harvest_date"]),
            storage_type=batch.get("storage_type", "ambient"),
            current_temp=batch.get("storage_temp"),
            current_humidity=batch.get("storage_humidity"),
        )
        batch["spoilage_risk"] = spoilage["spoilage_risk"]
        batch["spoilage_probability"] = spoilage["spoilage_probability"]
        batch["estimated_shelf_life_days"] = spoilage["estimated_shelf_life_days"]

    return batch


@router.post("/batches/{batch_id}/images")
async def upload_produce_image(
    batch_id: int,
    file: UploadFile = File(...),
):
    """Upload a produce image and run quality assessment."""
    if batch_id not in _batches:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch = _batches[batch_id]
    image_bytes = await file.read()

    # Run quality assessment
    assessment = await quality_service.assess_quality_from_image(
        image_bytes, batch["crop_name"]
    )

    # Update batch with quality data
    batch["quality_grade"] = assessment["overall_grade"]
    batch["quality_score"] = assessment["quality_score"]

    return {
        "batch_id": batch_id,
        "crop_name": batch["crop_name"],
        **assessment,
    }
