"""
Quality assessment endpoints.
Image-based produce quality analysis using custom MobileNetV2 freshness model.
Falls back to Rekognition/simulation when model is unavailable.

Includes integrated quality → price recommendation pipeline:
    Upload photo → freshness detection → mandi-grounded price recommendation.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import Optional
from datetime import date, timezone, datetime

from app.services.quality_service import quality_service
from app.services.pricing_service import pricing_service
from app.services.mandi_service import mandi_client
from app.api.routes.produce import _batches

router = APIRouter()


@router.get("/model-status")
async def model_status():
    """
    Check which freshness detection model is loaded.
    Returns model type (onnx/pytorch/none) and supported crops.
    """
    return quality_service.get_model_status()


@router.post("/assess/{batch_id}")
async def assess_quality(
    batch_id: int,
    file: UploadFile = File(...),
):
    """
    Upload a produce image and get AI quality/freshness assessment.
    Uses custom MobileNetV2 model → Rekognition → simulation fallback.

    Returns freshness status, confidence, quality grade, and Hindi+English recommendations.
    """
    if batch_id not in _batches:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch = _batches[batch_id]
    image_bytes = await file.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty image file")

    if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

    result = await quality_service.assess_quality_from_image(
        image_bytes, batch["crop_name"]
    )

    # Update batch quality data
    batch["quality_grade"] = result["overall_grade"]
    batch["quality_score"] = result["quality_score"]
    if "freshness_status" in result:
        batch["freshness_status"] = result["freshness_status"]

    return {
        "batch_id": batch_id,
        "crop_name": batch["crop_name"],
        **result,
    }


@router.post("/assess-standalone")
async def assess_quality_standalone(
    crop_name: str = Query(..., description="Crop name (e.g., tomato, mango, apple)"),
    file: UploadFile = File(...),
):
    """
    Assess quality without a batch — upload a photo and crop name.
    Good for quick freshness checks before registering a batch.
    """
    image_bytes = await file.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty image file")

    try:
        result = await quality_service.assess_quality_from_image(image_bytes, crop_name)
    except Exception as e:
        print(f"⚠ All vision backends failed ({e}), using simulation fallback")
        result = quality_service._simulate_assessment(crop_name)

    return {
        "crop_name": crop_name,
        **result,
    }


@router.get("/simulate/{crop_name}")
async def simulate_quality(crop_name: str):
    """
    Simulated quality assessment (no image needed).
    Useful for demo and testing.
    """
    result = quality_service._simulate_assessment(crop_name)
    return {
        "crop_name": crop_name,
        **result,
        "note": "This is a simulated assessment. Upload an actual image for real analysis.",
    }


# ═══════════════════════════════════════════════════════════
#   Integrated: Quality → Price Recommendation
# ═══════════════════════════════════════════════════════════


QUALITY_GRADE_TO_SPOILAGE = {
    "excellent": "low",
    "good": "low",
    "average": "medium",
    "poor": "high",
}


@router.post("/assess-and-price/{batch_id}")
async def assess_quality_and_recommend_price(
    batch_id: int,
    file: UploadFile = File(...),
):
    """
    Full pipeline: Upload produce photo → AI freshness detection →
    mandi-grounded price recommendation.

    1. Runs freshness model on the image
    2. Maps quality grade to pricing parameters
    3. Fetches live mandi prices for the crop
    4. Generates AI price recommendation using XGBoost

    Returns both quality assessment and price recommendation in one response.
    """
    if batch_id not in _batches:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch = _batches[batch_id]
    image_bytes = await file.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty image file")
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

    # ── Step 1: Freshness detection ──────────────────────────
    try:
        quality_result = await quality_service.assess_quality_from_image(
            image_bytes, batch["crop_name"]
        )
    except Exception as e:
        print(f"⚠ All vision backends failed ({e}), using simulation fallback")
        quality_result = quality_service._simulate_assessment(batch["crop_name"])

    # Update batch with quality data
    batch["quality_grade"] = quality_result["overall_grade"]
    batch["quality_score"] = quality_result["quality_score"]
    if "freshness_status" in quality_result:
        batch["freshness_status"] = quality_result["freshness_status"]

    # ── Step 2: Map quality → pricing inputs ─────────────────
    quality_grade = quality_result["overall_grade"]
    spoilage_risk = QUALITY_GRADE_TO_SPOILAGE.get(quality_grade, "medium")

    harvest_date = batch.get("harvest_date")
    if isinstance(harvest_date, str):
        harvest_date = date.fromisoformat(harvest_date)

    # ── Step 3: Generate price recommendation ────────────────
    price_rec = pricing_service.generate_price_recommendation(
        crop_name=batch["crop_name"],
        quantity_kg=batch["quantity_kg"],
        quality_grade=quality_grade,
        spoilage_risk=spoilage_risk,
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
        "crop_name": batch["crop_name"],
        "quality_assessment": quality_result,
        "price_recommendation": {
            **price_rec,
            "quality_based_note": _quality_price_note(quality_grade, price_rec),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/assess-and-price")
async def assess_quality_and_recommend_price_standalone(
    crop_name: str = Query(..., description="Crop name (e.g., tomato, mango, apple)"),
    quantity_kg: float = Query(default=100, gt=0, description="Quantity in kg"),
    file: UploadFile = File(...),
    storage_type: Optional[str] = Query(default="ambient", description="ambient, cold, controlled"),
    state: Optional[str] = Query(default=None, description="State for mandi price lookup"),
):
    """
    Standalone pipeline (no batch needed): Upload photo + crop name →
    freshness detection → mandi price recommendation.

    Perfect for farmers who want a quick price check from a photo.
    """
    image_bytes = await file.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty image file")
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

    # ── Step 1: Freshness detection ──────────────────────────
    try:
        quality_result = await quality_service.assess_quality_from_image(
            image_bytes, crop_name
        )
    except Exception as e:
        # Fallback to simulation when all vision backends fail (e.g. AWS_ONLY mode)
        print(f"⚠ All vision backends failed ({e}), using simulation fallback")
        quality_result = quality_service._simulate_assessment(crop_name)

    # ── Step 2: Map quality → pricing inputs ─────────────────
    quality_grade = quality_result["overall_grade"]
    spoilage_risk = QUALITY_GRADE_TO_SPOILAGE.get(quality_grade, "medium")

    # ── Step 3: Generate price recommendation ────────────────
    price_rec = pricing_service.generate_price_recommendation(
        crop_name=crop_name,
        quantity_kg=quantity_kg,
        quality_grade=quality_grade,
        spoilage_risk=spoilage_risk,
        storage_type=storage_type or "ambient",
    )

    # ── Step 4: Also fetch raw mandi prices ──────────────────
    mandi_prices = await mandi_client.fetch_prices(crop_name, state=state, limit=10)

    return {
        "crop_name": crop_name,
        "quantity_kg": quantity_kg,
        "quality_assessment": quality_result,
        "price_recommendation": {
            **price_rec,
            "quality_based_note": _quality_price_note(quality_grade, price_rec),
        },
        "mandi_prices": {
            "records": mandi_prices.get("records", [])[:5],
            "total_mandis": mandi_prices.get("total", 0),
            "source": mandi_prices.get("source", "simulated"),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/simulate-and-price/{crop_name}")
async def simulate_quality_and_recommend_price(
    crop_name: str,
    quantity_kg: float = Query(default=100, gt=0),
    storage_type: Optional[str] = Query(default="ambient"),
    state: Optional[str] = Query(default=None, description="State for mandi prices"),
):
    """
    Demo-friendly endpoint: simulated quality detection → price recommendation.

    No image upload required — uses simulation to generate quality grades,
    then feeds them into the ML pricing engine with live mandi data.
    """
    # Simulated quality
    quality_result = quality_service._simulate_assessment(crop_name)

    quality_grade = quality_result["overall_grade"]
    spoilage_risk = QUALITY_GRADE_TO_SPOILAGE.get(quality_grade, "medium")

    # Price recommendation
    price_rec = pricing_service.generate_price_recommendation(
        crop_name=crop_name,
        quantity_kg=quantity_kg,
        quality_grade=quality_grade,
        spoilage_risk=spoilage_risk,
        storage_type=storage_type or "ambient",
    )

    # Live mandi prices
    mandi_prices = await mandi_client.fetch_prices(crop_name, state=state, limit=10)

    return {
        "crop_name": crop_name,
        "quantity_kg": quantity_kg,
        "quality_assessment": {
            **quality_result,
            "note": "Simulated — upload a real image for accurate assessment",
        },
        "price_recommendation": {
            **price_rec,
            "quality_based_note": _quality_price_note(quality_grade, price_rec),
        },
        "mandi_prices": {
            "records": mandi_prices.get("records", [])[:5],
            "total_mandis": mandi_prices.get("total", 0),
            "source": mandi_prices.get("source", "simulated"),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _quality_price_note(grade: str, price_rec: dict) -> str:
    """Generate a human-readable note linking quality to price."""
    ideal = price_rec.get("ideal_price", 0)
    source = price_rec.get("price_source", "simulated")
    source_label = "live mandi data" if source == "data.gov.in" else "estimated market data"

    notes = {
        "excellent": (
            f"Excellent quality detected! Your produce can command premium prices. "
            f"Based on {source_label}, ideal selling price is ₹{ideal}/kg."
        ),
        "good": (
            f"Good quality produce. You should get fair market rates. "
            f"Based on {source_label}, recommended price is ₹{ideal}/kg."
        ),
        "average": (
            f"Average quality — consider selling quickly before further deterioration. "
            f"Based on {source_label}, realistic price is ₹{ideal}/kg."
        ),
        "poor": (
            f"Quality is poor — sell immediately or route to processing units. "
            f"Based on {source_label}, expected price is ₹{ideal}/kg."
        ),
    }
    return notes.get(grade, f"Recommended price: ₹{ideal}/kg based on {source_label}.")