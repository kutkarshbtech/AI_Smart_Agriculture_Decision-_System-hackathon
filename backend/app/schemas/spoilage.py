"""
Pydantic schemas for Spoilage & Quality endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class SpoilageAssessmentRequest(BaseModel):
    batch_id: int
    current_temp: Optional[float] = Field(None, description="Current temperature °C")
    current_humidity: Optional[float] = Field(None, description="Current humidity %")
    hours_since_harvest: Optional[float] = None
    transport_hours: Optional[float] = Field(default=0, description="Hours in transit")
    has_cold_storage: bool = False


class SpoilageAssessmentResponse(BaseModel):
    batch_id: int
    crop_name: str
    spoilage_risk: str = Field(..., description="low, medium, high, critical")
    spoilage_probability: float = Field(..., ge=0, le=1)
    estimated_shelf_life_days: int
    remaining_shelf_life_days: int
    risk_factors: List[Dict[str, Any]] = Field(
        default=[],
        description="Factors contributing to spoilage risk"
    )
    recommendations: List[str] = Field(
        default=[],
        description="Actions to reduce spoilage"
    )
    explanation: str = Field(
        ..., description="Causal explanation of spoilage risk"
    )


class QualityAssessmentResponse(BaseModel):
    batch_id: int
    crop_name: str
    overall_grade: str = Field(..., description="excellent, good, average, poor")
    quality_score: float = Field(..., ge=0, le=100)
    freshness_score: float = Field(..., ge=0, le=100)
    damage_score: float = Field(
        ..., ge=0, le=100,
        description="Higher = more damage detected"
    )
    ripeness_level: str = Field(
        ..., description="unripe, ripe, overripe"
    )
    defects_detected: List[str] = Field(default=[])
    analysis_summary: str
    image_annotations_url: Optional[str] = None


class ColdChainRecommendation(BaseModel):
    batch_id: int
    recommended_storage: str = Field(
        ..., description="cold_storage, ambient, controlled_atmosphere"
    )
    recommended_temp: float
    recommended_humidity: float
    nearest_cold_storage: Optional[Dict[str, Any]] = None
    routes: List[Dict[str, Any]] = Field(
        default=[],
        description="Suggested routes with cost and spoilage tradeoff"
    )
    estimated_cost: Optional[float] = None
    spoilage_reduction_percent: Optional[float] = None
