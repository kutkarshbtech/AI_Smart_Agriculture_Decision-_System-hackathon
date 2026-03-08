"""
Authentication API routes for mobile number + OTP login using PostgreSQL.
Endpoints for Buyer, Seller, and Logistic Provider registration/login.
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.schemas.auth import (
    RegisterRequest, LoginRequest, VerifyOTPRequest, OTPResponse, 
    AuthToken, UserProfile, UpdateProfileRequest
)
from app.services.auth_service import AuthService
from app.core.database import get_db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Initialize auth service
auth_service = AuthService()


@router.post("/register", response_model=dict)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user (Buyer, Seller, or Logistic Provider)
    
    - **mobile_number**: Mobile number with country code (e.g., +919876543210)
    - **user_type**: One of "buyer", "seller", "logistic"
    - **name**: Full name of the user
    - **business_name**: Optional business name (for buyers/logistics)
    - **vehicle_types**: Optional list of vehicle types (for logistics)
    - **operating_states**: Optional states where they operate
    """
    # Prepare additional fields
    additional_fields = {}
    if request.business_name:
        additional_fields['business_name'] = request.business_name
    if request.vehicle_types:
        additional_fields['vehicle_types'] = request.vehicle_types
    if request.operating_states:
        additional_fields['operating_states'] = request.operating_states
    if request.city:
        additional_fields['city'] = request.city
    if request.state:
        additional_fields['state'] = request.state
    if request.pincode:
        additional_fields['pincode'] = request.pincode
    
    success, message, user_data = await auth_service.register_user(
        db=db,
        mobile_number=request.mobile_number,
        user_type=request.user_type,
        name=request.name,
        **additional_fields
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "user": {
            "id": user_data['id'],
            "mobile_number": user_data['mobile_number'],
            "user_type": user_data['user_type'],
            "name": user_data['name']
        }
    }


@router.post("/login/request-otp", response_model=OTPResponse)
async def request_otp(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Request OTP for login
    
    - **mobile_number**: Registered mobile number
    - **user_type**: One of "buyer", "seller", "logistic"
    
    Returns OTP in demo mode (remove in production!)
    """
    success, message, otp = await auth_service.send_otp(
        db=db,
        mobile_number=request.mobile_number,
        user_type=request.user_type
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return OTPResponse(
        success=True,
        message=message,
        otp_sent=True,
        demo_otp=otp  # Only for demo! Remove in production
    )


@router.post("/login/verify-otp", response_model=AuthToken)
async def verify_otp(request: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify OTP and complete login
    
    - **mobile_number**: Mobile number
    - **user_type**: One of "buyer", "seller", "logistic"
    - **otp**: 6-digit OTP received
    
    Returns authentication token for future requests
    """
    success, message, token = await auth_service.verify_otp(
        db=db,
        mobile_number=request.mobile_number,
        user_type=request.user_type,
        otp=request.otp
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Get user data
    user = await auth_service.get_user(db, request.mobile_number, request.user_type)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return AuthToken(
        access_token=token,
        token_type="bearer",
        user_id=user['id'],
        user_type=user['user_type'],
        name=user['name'],
        mobile_number=user['mobile_number']
    )


@router.get("/profile", response_model=UserProfile)
async def get_profile(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    """
    Get user profile (requires authentication)
    
    Pass token in Authorization header: "Bearer <token>"
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    valid, user_data = await auth_service.verify_token(db, token)
    
    if not valid or not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return UserProfile(**user_data)


@router.put("/profile", response_model=dict)
async def update_profile(
    request: UpdateProfileRequest, 
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user profile (requires authentication)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    valid, user_data = await auth_service.verify_token(db, token)
    
    if not valid or not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Update profile
    updates = request.dict(exclude_unset=True)
    success, message = await auth_service.update_user(
        db=db,
        mobile_number=user_data['mobile_number'],
        user_type=user_data['user_type'],
        **updates
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message
    }


@router.post("/logout", response_model=dict)
async def logout(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    """
    Logout user (invalidate token)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    success = await auth_service.logout(db, token)
    
    return {
        "success": success,
        "message": "Logged out successfully" if success else "Token not found"
    }


@router.get("/users/{user_type}", response_model=list[UserProfile])
async def get_users_by_type(user_type: str, db: AsyncSession = Depends(get_db)):
    """
    Get all users of a specific type (for admin/demo purposes)
    
    - **user_type**: One of "buyer", "seller", "logistic"
    """
    if user_type not in ["buyer", "seller", "logistic"]:
        raise HTTPException(status_code=400, detail="Invalid user type")
    
    users = await auth_service.get_all_users_by_type(db, user_type)
    return [UserProfile(**user) for user in users]
