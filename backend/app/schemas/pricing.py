"""
Pydantic schemas for Pricing endpoints.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime


class MarketPriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crop_name: str
    mandi_name: str
    district: Optional[str] = None
    state: Optional[str] = None
    min_price: float  # ₹/quintal
    max_price: float
    modal_price: float
    date: date
    source: str


class PriceRecommendationRequest(BaseModel):
    """Direct price recommendation without a batch."""
    crop_name: str = Field(..., description="Name of the crop (e.g., tomato, onion)")
    quantity_kg: float = Field(..., gt=0, description="Quantity in kg")
    harvest_date: Optional[date] = Field(None, description="Date of harvest")
    quality_grade: Optional[str] = Field(None, description="excellent, good, average, poor")
    spoilage_risk: Optional[str] = Field(None, description="low, medium, high, critical")
    remaining_shelf_life_days: Optional[int] = None
    storage_type: Optional[str] = Field(None, description="ambient, cold, controlled")
    storage_temp: Optional[float] = None
    storage_humidity: Optional[float] = None
    farmer_location_lat: Optional[float] = None
    farmer_location_lng: Optional[float] = None


class PriceFactor(BaseModel):
    """An individual factor that influences the price recommendation."""
    name: str = Field(..., description="Factor name (e.g., 'Quality Grade')")
    value: str = Field(..., description="Factor value (e.g., 'good')")
    impact: str = Field(..., description="baseline, positive, negative, neutral, reference, protection")
    weight: Optional[float] = Field(None, ge=0, le=1, description="Relative weight of this factor")


class WhatIfScenario(BaseModel):
    """A causal what-if scenario showing price impact."""
    scenario: str = Field(..., description="Scenario description")
    price_change: str = Field(..., description="Price change like '+₹2.50/kg (+8.5%)'")
    new_ideal_price: float
    recommendation: str


class PriceForecastDay(BaseModel):
    """Single-day price forecast."""
    date: str
    predicted_price: float
    confidence: float
    trend: str


class PriceRecommendationResponse(BaseModel):
    batch_id: Optional[int] = None
    crop_name: str
    quantity_kg: float
    recommended_min_price: float = Field(
        ..., description="Seller-protected floor price ₹/kg"
    )
    recommended_max_price: float = Field(
        ..., description="Upper end of recommended range ₹/kg"
    )
    ideal_price: float = Field(
        ..., description="AI-predicted ideal selling price ₹/kg"
    )
    price_range_lower: float = Field(
        ..., description="Confidence interval lower bound ₹/kg"
    )
    price_range_upper: float = Field(
        ..., description="Confidence interval upper bound ₹/kg"
    )
    predicted_market_price: Optional[float] = None
    confidence_score: float = Field(..., ge=0, le=1)
    factors: List[Dict[str, Any]] = Field(
        default=[],
        description="Factors affecting the price recommendation with weights"
    )
    recommendation_text: str = Field(
        ..., description="Human-readable recommendation"
    )
    action: str = Field(
        ..., description="sell_now, wait, or store",
        examples=["sell_now"]
    )
    action_text: Optional[str] = Field(
        None, description="Detailed action explanation"
    )
    msp_note: Optional[str] = Field(
        None, description="Note about Minimum Support Price"
    )
    demand_index: Optional[float] = Field(
        None, description="Current market demand index (0-1)"
    )
    price_forecast_3d: Optional[List[Dict[str, Any]]] = Field(
        None, description="3-day price forecast"
    )
    what_if_scenarios: Optional[List[Dict[str, Any]]] = Field(
        None, description="Causal what-if scenarios"
    )
    valid_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    trend: Optional[str] = None
    avg_7d: Optional[float] = None
    model_type: Optional[str] = Field(
        None, description="Model used: 'xgboost' or 'rule_based'"
    )
    price_source: Optional[str] = Field(
        None, description="Price data source: 'data.gov.in' or 'simulated'"
    )

    model_config = ConfigDict(from_attributes=True)


class PriceTrendResponse(BaseModel):
    crop_name: str
    mandi_name: Optional[str] = None
    prices: List[MarketPriceResponse] = []
    trend: str = Field(..., description="rising, falling, stable")
    avg_price_7d: Optional[float] = None
    avg_price_30d: Optional[float] = None


class PriceForecastResponse(BaseModel):
    crop_name: str
    current_trend: str
    forecast: List[PriceForecastDay]


class WhatIfRequest(BaseModel):
    """Request for causal what-if analysis."""
    crop_name: str
    quantity_kg: float
    harvest_date: Optional[date] = None
    quality_grade: Optional[str] = None
    spoilage_risk: Optional[str] = None
    # Override fields for what-if
    new_storage_temp: Optional[float] = Field(None, description="What if temperature changes?")
    new_quality_grade: Optional[str] = Field(None, description="What if quality changes?")
    new_storage_type: Optional[str] = Field(None, description="What if storage changes?")


class WhatIfResponse(BaseModel):
    original_ideal_price: float
    new_ideal_price: float
    price_change: float
    price_change_pct: float
    overrides_applied: Dict[str, Any]


# ─── Mandi (data.gov.in) ─────────────────────────────────


class MandiPriceRecord(BaseModel):
    """A single mandi price record from data.gov.in."""
    state: str = ""
    district: str = ""
    market: str = ""
    commodity: str = ""
    variety: str = ""
    arrival_date: str = ""
    min_price_per_quintal: float = 0
    max_price_per_quintal: float = 0
    modal_price_per_quintal: float = 0
    min_price_per_kg: float = 0
    max_price_per_kg: float = 0
    modal_price_per_kg: float = 0
    source: str = "data.gov.in"


class MandiPriceListResponse(BaseModel):
    """Response from the mandi price API."""
    commodity: str
    records: List[MandiPriceRecord] = []
    total: int = 0
    source: str = "data.gov.in"
    cached: bool = False
    api_error: Optional[str] = None


class MandiPriceSummary(BaseModel):
    """Aggregated price summary across mandis."""
    commodity: str
    num_mandis: int = 0
    avg_price_per_kg: Optional[float] = None
    min_price_per_kg: Optional[float] = None
    max_price_per_kg: Optional[float] = None
    modal_price_per_kg: Optional[float] = None
    states: List[str] = []
    source: str = "data.gov.in"
    api_error: Optional[str] = None
