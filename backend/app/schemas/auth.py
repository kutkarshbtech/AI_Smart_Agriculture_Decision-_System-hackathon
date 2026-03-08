"""
Authentication schemas for mobile number + OTP login.
Supports three user types: Buyer, Seller, Logistic Provider
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime
import re


class RegisterRequest(BaseModel):
    """Register a new user with mobile number"""
    mobile_number: str = Field(..., min_length=10, max_length=15, 
                                description="Mobile number with country code")
    user_type: Literal["buyer", "seller", "logistic"] = Field(..., 
                                                                description="Type of user")
    name: str = Field(..., min_length=2, max_length=100)
    
    # Optional fields based on user type
    business_name: Optional[str] = Field(None, max_length=200, 
                                         description="For buyers/logistics")
    vehicle_types: Optional[list[str]] = Field(None, 
                                               description="For logistics providers")
    operating_states: Optional[list[str]] = Field(None, 
                                                  description="States where they operate")
    
    # Location
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = Field(None, pattern=r"^\d{6}$")
    
    @validator('mobile_number')
    def validate_mobile(cls, v):
        # Remove spaces and special characters
        cleaned = re.sub(r'[^0-9+]', '', v)
        if not re.match(r'^\+?[1-9]\d{9,14}$', cleaned):
            raise ValueError('Invalid mobile number format')
        return cleaned


class LoginRequest(BaseModel):
    """Request OTP for login"""
    mobile_number: str = Field(..., min_length=10, max_length=15)
    user_type: Literal["buyer", "seller", "logistic"]
    
    @validator('mobile_number')
    def validate_mobile(cls, v):
        cleaned = re.sub(r'[^0-9+]', '', v)
        if not re.match(r'^\+?[1-9]\d{9,14}$', cleaned):
            raise ValueError('Invalid mobile number format')
        return cleaned


class VerifyOTPRequest(BaseModel):
    """Verify OTP and complete login"""
    mobile_number: str
    user_type: Literal["buyer", "seller", "logistic"]
    otp: str = Field(..., min_length=4, max_length=6, pattern=r'^\d+$')


class OTPResponse(BaseModel):
    """Response after requesting OTP"""
    success: bool
    message: str
    otp_sent: bool
    # In demo mode, we return the OTP for testing (remove in production!)
    demo_otp: Optional[str] = None


class AuthToken(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    user_type: str
    name: str
    mobile_number: str
    expires_in: int = 86400  # 24 hours in seconds


class UserProfile(BaseModel):
    """User profile information"""
    id: int
    mobile_number: str
    user_type: str
    name: str
    business_name: Optional[str] = None
    vehicle_types: Optional[list[str]] = None
    operating_states: Optional[list[str]] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """Update user profile"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    business_name: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = Field(None, pattern=r"^\d{6}$")
    vehicle_types: Optional[list[str]] = None
    operating_states: Optional[list[str]] = None
