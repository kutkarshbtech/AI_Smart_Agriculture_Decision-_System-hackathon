"""
Feature engineering for the price prediction model.
Transforms raw batch + market data into ML-ready features.
"""
from datetime import date, timedelta
from typing import Dict, Any, Optional, List
import math


# Government Minimum Support Prices (₹/quintal → ₹/kg) – 2024-25 season
# Source: https://farmer.gov.in/mspstatements.aspx
MSP_DATA: Dict[str, float] = {
    "rice": 23.20,     # ₹2320/quintal paddy (raw)
    "wheat": 23.25,    # ₹2325/quintal
    "jowar": 33.71,
    "bajra": 26.25,
    "maize": 21.82,
    "ragi": 40.54,
    "moong": 82.82,
    "urad": 72.00,
    "groundnut": 62.00,
    "soybean": 47.00,
    "sunflower": 70.00,
    "mustard": 57.50,
    "cotton": 72.05,
    "sugarcane": 3.40,
}

# Average shelf life baseline (days) by crop
SHELF_LIFE_DAYS: Dict[str, int] = {
    "tomato": 7, "potato": 30, "onion": 30, "banana": 5, "mango": 5,
    "apple": 14, "rice": 365, "wheat": 180, "cauliflower": 4, "spinach": 2,
    "capsicum": 5, "okra": 3, "brinjal": 5, "guava": 5, "grape": 3, "carrot": 7,
}

# Perishability index (0 = non-perishable, 1 = highly perishable)
PERISHABILITY_INDEX: Dict[str, float] = {
    "tomato": 0.75, "potato": 0.15, "onion": 0.20, "banana": 0.85,
    "mango": 0.80, "apple": 0.40, "rice": 0.02, "wheat": 0.03,
    "cauliflower": 0.90, "spinach": 0.95, "capsicum": 0.70,
    "okra": 0.80, "brinjal": 0.65, "guava": 0.75, "grape": 0.85, "carrot": 0.50,
}

# One-hot categories
CROP_CATEGORIES = {"vegetable": 0, "fruit": 1, "grain": 2, "spice": 3}
STORAGE_TYPES = {"ambient": 0, "cold": 1, "controlled": 2}
QUALITY_GRADES = {"excellent": 3, "good": 2, "average": 1, "poor": 0}
SEASONS = {"summer": 0, "monsoon": 1, "spring": 2, "winter": 3}


def get_season(d: date) -> str:
    month = d.month
    if month in (3, 4, 5):
        return "summer"
    elif month in (6, 7, 8, 9):
        return "monsoon"
    elif month in (10, 11):
        return "spring"
    return "winter"


def days_since_harvest(harvest_date: date, reference: Optional[date] = None) -> int:
    ref = reference or date.today()
    return max((ref - harvest_date).days, 0)


def remaining_shelf_life_ratio(crop_name: str, harvest_date: date) -> float:
    """Fraction of shelf life remaining (0-1)."""
    total = SHELF_LIFE_DAYS.get(crop_name.lower(), 7)
    elapsed = days_since_harvest(harvest_date)
    return max(0.0, (total - elapsed) / total)


def build_features(
    crop_name: str,
    quantity_kg: float,
    harvest_date: date,
    storage_type: str = "ambient",
    storage_temp: Optional[float] = None,
    storage_humidity: Optional[float] = None,
    quality_grade: Optional[str] = None,
    spoilage_risk: Optional[str] = None,
    spoilage_probability: Optional[float] = None,
    remaining_shelf_life_days: Optional[int] = None,
    farmer_lat: Optional[float] = None,
    farmer_lng: Optional[float] = None,
    market_price_today: Optional[float] = None,
    market_price_avg_7d: Optional[float] = None,
    demand_index: Optional[float] = None,
) -> Dict[str, float]:
    """
    Build a feature vector for the price prediction model.

    Returns a dictionary of feature_name → float value.
    """
    crop = crop_name.lower()
    today = date.today()
    season = get_season(today)

    features: Dict[str, float] = {}

    # --- Temporal features ---
    features["day_of_week"] = today.weekday()  # 0=Mon, 6=Sun
    features["day_of_month"] = today.day
    features["month"] = today.month
    features["season_code"] = SEASONS.get(season, 0)
    features["is_weekend"] = 1.0 if today.weekday() >= 5 else 0.0

    # --- Crop intrinsic features ---
    features["perishability"] = PERISHABILITY_INDEX.get(crop, 0.5)
    features["base_shelf_life"] = float(SHELF_LIFE_DAYS.get(crop, 7))
    features["has_msp"] = 1.0 if crop in MSP_DATA else 0.0
    features["msp_per_kg"] = MSP_DATA.get(crop, 0.0)

    # --- Batch-specific features ---
    features["quantity_kg"] = quantity_kg
    features["log_quantity"] = math.log1p(quantity_kg)
    features["days_since_harvest"] = float(days_since_harvest(harvest_date))
    features["shelf_life_remaining_ratio"] = remaining_shelf_life_ratio(crop, harvest_date)

    if remaining_shelf_life_days is not None:
        features["remaining_shelf_life_days"] = float(remaining_shelf_life_days)
    else:
        total = SHELF_LIFE_DAYS.get(crop, 7)
        elapsed = days_since_harvest(harvest_date)
        features["remaining_shelf_life_days"] = float(max(total - elapsed, 0))

    # --- Storage features ---
    features["storage_type_code"] = float(STORAGE_TYPES.get(storage_type, 0))
    features["is_cold_storage"] = 1.0 if storage_type in ("cold", "controlled") else 0.0

    if storage_temp is not None:
        features["storage_temp"] = storage_temp
    else:
        features["storage_temp"] = 25.0 if storage_type == "ambient" else 4.0

    if storage_humidity is not None:
        features["storage_humidity"] = storage_humidity
    else:
        features["storage_humidity"] = 60.0

    # --- Quality features ---
    features["quality_code"] = float(QUALITY_GRADES.get(quality_grade or "average", 1))
    features["spoilage_prob"] = spoilage_probability if spoilage_probability is not None else 0.3

    spoilage_risk_map = {"low": 0.0, "medium": 0.33, "high": 0.66, "critical": 1.0}
    features["spoilage_risk_code"] = spoilage_risk_map.get(spoilage_risk or "medium", 0.33)

    # --- Market context features ---
    features["market_price_today"] = market_price_today if market_price_today is not None else 0.0
    features["market_price_avg_7d"] = market_price_avg_7d if market_price_avg_7d is not None else 0.0
    if market_price_today and market_price_avg_7d and market_price_avg_7d > 0:
        features["price_momentum"] = (market_price_today - market_price_avg_7d) / market_price_avg_7d
    else:
        features["price_momentum"] = 0.0

    features["demand_index"] = demand_index if demand_index is not None else 0.5

    return features


# Ordered feature list for the model (must match training order)
FEATURE_NAMES: List[str] = [
    "day_of_week", "day_of_month", "month", "season_code", "is_weekend",
    "perishability", "base_shelf_life", "has_msp", "msp_per_kg",
    "quantity_kg", "log_quantity", "days_since_harvest", "shelf_life_remaining_ratio",
    "remaining_shelf_life_days",
    "storage_type_code", "is_cold_storage", "storage_temp", "storage_humidity",
    "quality_code", "spoilage_prob", "spoilage_risk_code",
    "market_price_today", "market_price_avg_7d", "price_momentum",
    "demand_index",
]


def features_to_vector(features: Dict[str, float]) -> List[float]:
    """Convert feature dict to ordered list matching the model's expected input."""
    return [features.get(name, 0.0) for name in FEATURE_NAMES]
