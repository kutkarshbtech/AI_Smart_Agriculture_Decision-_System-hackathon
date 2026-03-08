"""
Pydantic schemas for User / Farmer endpoints.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15, examples=["+919876543210"])
    name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="farmer")
    language: str = Field(default="hi", description="ISO 639-1 language code")
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pin_code: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    phone: str
    name: str
    role: str
    language: str
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pin_code: Optional[str] = None
