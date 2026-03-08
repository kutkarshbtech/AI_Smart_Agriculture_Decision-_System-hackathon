"""
Pydantic schemas for Buyer matching, Offers, & Alert endpoints.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─── Buyer Matching ──────────────────────────────────────

class BuyerCreate(BaseModel):
    shop_name: Optional[str] = None
    contact_phone: str = Field(..., min_length=10, max_length=15)
    contact_name: str
    buyer_type: str = Field(default="retailer", description="retailer, wholesaler, aggregator")
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    preferred_crops: List[str] = Field(default=[], description="List of crop names")
    max_quantity_kg: Optional[float] = None
    languages: List[str] = Field(default=["hi"])
    payment_modes: List[str] = Field(default=["cash"])
    accepts_delivery: bool = False


class BuyerSubScores(BaseModel):
    """Sub-scores for the buyer match."""
    proximity: float = Field(..., ge=0, le=100)
    rating: float = Field(..., ge=0, le=100)
    capacity_fit: float = Field(..., ge=0, le=100)
    payment_speed: float = Field(..., ge=0, le=100)
    demand_urgency: float = Field(..., ge=0, le=100)
    reliability: float = Field(..., ge=0, le=100)


class ActiveDemandInfo(BaseModel):
    """Active demand info attached to a buyer match."""
    quantity_needed_kg: float
    max_price_per_kg: float
    urgency: str
    valid_until: str


class BuyerResponse(BaseModel):
    id: int
    shop_name: Optional[str] = None
    buyer_type: str = "retailer"
    contact_name: str
    contact_phone: str
    district: Optional[str] = None
    state: Optional[str] = None
    distance_km: Optional[float] = None
    max_quantity_kg: Optional[float] = None
    preferred_crops: List[str] = []
    is_verified: bool = True
    rating: float = 0.0
    total_transactions: int = 0
    avg_payment_days: int = 0
    languages: List[str] = []
    operating_hours: str = ""
    accepts_delivery: bool = False
    payment_modes: List[str] = []
    match_score: Optional[float] = Field(None, description="Composite match score 0-100")
    sub_scores: Optional[Dict[str, float]] = Field(
        None, description="Individual scoring breakdown"
    )
    has_active_demand: bool = False
    active_demand: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BuyerMatchRequest(BaseModel):
    batch_id: int
    farmer_lat: float
    farmer_lng: float
    max_distance_km: float = Field(default=50, description="Search radius in km")
    buyer_type: Optional[str] = Field(None, description="Filter: retailer, wholesaler, aggregator")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum buyer rating")
    sort_by: Optional[str] = Field(
        default="score",
        description="Sort by: 'score' (default), 'distance', 'rating'"
    )
    min_quantity_kg: Optional[float] = None


class BuyerMatchResponse(BaseModel):
    batch_id: int
    crop_name: str
    matched_buyers: List[BuyerResponse]
    total_matches: int


# ─── Active Demand ───────────────────────────────────────

class ActiveDemandResponse(BaseModel):
    demand_id: int
    buyer_id: int
    shop_name: str
    buyer_type: str = "retailer"
    district: str
    state: str
    crop_name: str
    quantity_needed_kg: float
    max_price_per_kg: float
    urgency: str = Field(..., description="high, medium, low")
    valid_until: str
    distance_km: Optional[float] = None
    buyer_rating: float = 0.0


# ─── Offers / Negotiation ───────────────────────────────

class OfferCreateRequest(BaseModel):
    farmer_id: int = Field(default=1, description="Farmer ID")
    buyer_id: int
    crop_name: str
    quantity_kg: float = Field(..., gt=0)
    asking_price_per_kg: float = Field(..., gt=0, description="Farmer's asking price ₹/kg")
    batch_id: Optional[int] = None
    notes: Optional[str] = None


class OfferUpdateRequest(BaseModel):
    status: str = Field(
        ..., description="accepted, rejected, or counter"
    )
    counter_price_per_kg: Optional[float] = Field(
        None, gt=0, description="Counter-offer price (required when status='counter')"
    )


class OfferResponse(BaseModel):
    id: int
    farmer_id: int
    buyer_id: int
    buyer_name: str
    crop_name: str
    quantity_kg: float
    asking_price_per_kg: float
    batch_id: Optional[int] = None
    status: str = Field(..., description="pending, accepted, counter, rejected, expired")
    counter_price_per_kg: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


# ─── Alerts ──────────────────────────────────────────────

class AlertResponse(BaseModel):
    id: int
    alert_type: str
    title: str
    message: str
    severity: str
    is_read: bool
    metadata: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertsListResponse(BaseModel):
    alerts: List[AlertResponse]
    unread_count: int
    total: int


# ─── Dashboard ───────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_batches: int
    active_batches: int
    sold_batches: int
    total_quantity_kg: float
    estimated_value: Optional[float] = None
    avg_quality_score: Optional[float] = None
    high_risk_batches: int
    pending_alerts: int
    top_recommendation: Optional[str] = None


# ─── Chatbot ─────────────────────────────────────────────

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    language: str = Field(default="hi", description="ISO 639-1 code")
    context: Optional[dict] = Field(
        default=None,
        description="Optional context like current batch_id, farmer location, etc."
    )


class ChatResponse(BaseModel):
    reply: str
    language: str
    suggested_actions: List[dict] = Field(
        default=[],
        description="Suggested quick actions for the farmer"
    )
    sources: List[str] = Field(
        default=[],
        description="Data sources referenced in the reply"
    )


class VoiceChatResponse(BaseModel):
    """Response for voice-based chat — includes transcript + chatbot reply."""
    transcript: str = Field(..., description="Transcribed text from the audio")
    transcript_confidence: float = Field(
        default=0.0, description="Average word confidence (0-1)"
    )
    detected_language: str = Field(
        default="hi-IN", description="Detected language code"
    )
    reply: str = Field(..., description="AI chatbot reply to the transcript")
    language: str = Field(default="hi", description="Response language")
    suggested_actions: List[dict] = Field(default=[])
    sources: List[str] = Field(default=[])
