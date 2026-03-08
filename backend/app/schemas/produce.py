"""
Pydantic schemas for Produce / Batch endpoints.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import date, datetime


class ProduceBatchCreate(BaseModel):
    crop_type_id: int
    quantity_kg: float = Field(..., gt=0, description="Quantity in kilograms")
    harvest_date: date
    storage_type: str = Field(default="ambient", description="ambient, cold, controlled")
    storage_temp: Optional[float] = Field(None, description="Current storage temp °C")
    storage_humidity: Optional[float] = Field(None, description="Current humidity %")
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    notes: Optional[str] = None


class ProduceBatchResponse(BaseModel):
    id: int
    farmer_id: int
    crop_type_id: int
    crop_name: Optional[str] = None
    quantity_kg: float
    harvest_date: date
    storage_type: str
    storage_temp: Optional[float] = None
    storage_humidity: Optional[float] = None
    quality_grade: Optional[str] = None
    quality_score: Optional[float] = None
    spoilage_risk: Optional[str] = None
    spoilage_probability: Optional[float] = None
    estimated_shelf_life_days: Optional[int] = None
    image_urls: List[str] = []
    is_sold: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProduceBatchUpdate(BaseModel):
    quantity_kg: Optional[float] = None
    storage_type: Optional[str] = None
    storage_temp: Optional[float] = None
    storage_humidity: Optional[float] = None
    is_sold: Optional[bool] = None
    notes: Optional[str] = None


class ProduceImageUpload(BaseModel):
    batch_id: int
    image_count: int = Field(default=1, ge=1, le=5)


class CropTypeResponse(BaseModel):
    id: int
    name_en: str
    name_hi: Optional[str] = None
    category: str
    avg_shelf_life_days: Optional[int] = None
    optimal_temp_min: Optional[float] = None
    optimal_temp_max: Optional[float] = None
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
