"""
Authentication Service with OTP-based mobile number login using PostgreSQL.
Handles registration, OTP generation/verification, and session management.
"""
import random
import string
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database_models import User, UserRole, OTPVerification, AuthToken


class AuthService:
    """Async authentication service for mobile OTP login with PostgreSQL"""
    
    @staticmethod
    def _generate_otp(length: int = 6) -> str:
        """Generate random OTP"""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def _generate_token() -> str:
        """Generate secure authentication token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def _map_user_type_to_role(user_type: str) -> UserRole:
        """Map user_type string to UserRole enum"""
        mapping = {
            "buyer": UserRole.BUYER,
            "seller": UserRole.SELLER,
            "farmer": UserRole.SELLER,  # Backward compatibility
            "logistic": UserRole.LOGISTIC,
            "fpo": UserRole.LOGISTIC,  # Backward compatibility
            "admin": UserRole.ADMIN
        }
        return mapping.get(user_type.lower(), UserRole.SELLER)
    
    async def register_user(
        self, 
        db: AsyncSession,
        mobile_number: str, 
        user_type: str, 
        name: str, 
        **additional_fields
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Register a new user
        
        Returns: (success, message, user_data)
        """
        # Check if user already exists
        stmt = select(User).where(User.phone == mobile_number)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            return False, "User already registered with this mobile number", None
        
        # Map user_type to UserRole
        role = self._map_user_type_to_role(user_type)
        
        # Create new user with role-specific fields
        user_data_dict = {
            "phone": mobile_number,
            "name": name,
            "role": role,
            "is_active": True,
            "city": additional_fields.get('city'),
            "state": additional_fields.get('state'),
            "pincode": additional_fields.get('pincode'),
            "business_name": additional_fields.get('business_name'),
            "vehicle_types": additional_fields.get('vehicle_types'),
            "operating_states": additional_fields.get('operating_states'),
            "village": additional_fields.get('village'),
            "district": additional_fields.get('district')
        }
        
        # Remove None values
        user_data_dict = {k: v for k, v in user_data_dict.items() if v is not None}
        
        new_user = User(**user_data_dict)
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        user_data = {
            "id": new_user.id,
            "mobile_number": new_user.phone,
            "user_type": user_type,
            "name": new_user.name,
            "role": new_user.role.value,
            "is_active": new_user.is_active,
            "created_at": new_user.created_at.isoformat() if new_user.created_at else None
        }
        
        return True, "User registered successfully", user_data
    
    async def send_otp(
        self, 
        db: AsyncSession,
        mobile_number: str, 
        user_type: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Send OTP to mobile number
        
        Returns: (success, message, otp_for_demo)
        """
        # Check if user exists
        stmt = select(User).where(User.phone == mobile_number)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return False, "User not registered. Please register first.", None
        
        # Delete any existing OTPs for this user
        delete_stmt = delete(OTPVerification).where(OTPVerification.user_id == user.id)
        await db.execute(delete_stmt)
        
        # Generate new OTP
        otp = self._generate_otp()
        
        # Store OTP with 5-minute expiry
        otp_record = OTPVerification(
            user_id=user.id,
            phone=mobile_number,
            otp_code=otp,
            is_verified=False,
            attempts=0,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
        )
        
        db.add(otp_record)
        await db.commit()
        
        # In production, send via AWS SNS
        # For demo, we return the OTP
        print(f"[AUTH] OTP for {mobile_number}: {otp}")
        
        return True, "OTP sent successfully", otp
    
    async def verify_otp(
        self, 
        db: AsyncSession,
        mobile_number: str, 
        user_type: str, 
        otp: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Verify OTP and generate auth token
        
        Returns: (success, message, auth_token)
        """
        # Get user
        stmt = select(User).where(User.phone == mobile_number)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return False, "User not found", None
        
        # Get OTP record
        otp_stmt = select(OTPVerification).where(
            OTPVerification.user_id == user.id,
            OTPVerification.is_verified == False
        ).order_by(OTPVerification.created_at.desc())
        otp_result = await db.execute(otp_stmt)
        otp_record = otp_result.scalar_one_or_none()
        
        if not otp_record:
            return False, "No OTP found. Please request a new one.", None
        
        # Check expiry (handle both naive and aware datetimes for PostgreSQL compatibility)
        _otp_expires = otp_record.expires_at if otp_record.expires_at.tzinfo else otp_record.expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > _otp_expires:
            await db.delete(otp_record)
            await db.commit()
            return False, "OTP expired. Please request a new one.", None
        
        # Check attempts (max 3)
        if otp_record.attempts >= 3:
            await db.delete(otp_record)
            await db.commit()
            return False, "Maximum attempts exceeded. Please request a new OTP.", None
        
        # Verify OTP
        if otp_record.otp_code != otp:
            otp_record.attempts += 1
            await db.commit()
            remaining = 3 - otp_record.attempts
            return False, f"Invalid OTP. {remaining} attempts remaining.", None
        
        # OTP verified - mark as verified and delete
        otp_record.is_verified = True
        await db.commit()
        await db.delete(otp_record)
        await db.commit()
        
        # Update user's last login time
        user.last_login = datetime.now(timezone.utc)
        await db.commit()
        
        # Generate auth token (valid for 24 hours)
        token = self._generate_token()
        auth_token = AuthToken(
            user_id=user.id,
            token=token,
            token_type="bearer",
            is_active=True,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1)
        )
        
        db.add(auth_token)
        await db.commit()
        
        return True, "Login successful", token
    
    async def verify_token(
        self, 
        db: AsyncSession,
        token: str
    ) -> Tuple[bool, Optional[dict]]:
        """
        Verify authentication token
        
        Returns: (valid, user_data)
        """
        # Get token record
        stmt = select(AuthToken).where(
            AuthToken.token == token,
            AuthToken.is_active == True
        )
        result = await db.execute(stmt)
        token_record = result.scalar_one_or_none()
        
        if not token_record:
            return False, None
        
        # Check expiry
        _expires = token_record.expires_at if token_record.expires_at.tzinfo else token_record.expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > _expires:
            token_record.is_active = False
            await db.commit()
            return False, None
        
        # Update last used
        token_record.last_used_at = datetime.now(timezone.utc)
        await db.commit()
        
        # Get user data
        user_stmt = select(User).where(User.id == token_record.user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return False, None
        
        user_data = {
            "id": user.id,
            "mobile_number": user.phone,
            "user_type": user.role.value,
            "name": user.name,
            "role": user.role.value,
            "business_name": user.business_name,
            "vehicle_types": user.vehicle_types,
            "operating_states": user.operating_states,
            "city": user.city,
            "village": user.village,
            "district": user.district,
            "state": user.state,
            "pincode": user.pincode,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
        return True, user_data
    
    async def get_user(
        self, 
        db: AsyncSession,
        mobile_number: str, 
        user_type: str
    ) -> Optional[dict]:
        """Get user data by phone"""
        stmt = select(User).where(User.phone == mobile_number)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        return {
            "id": user.id,
            "mobile_number": user.phone,
            "user_type": user.role.value,
            "name": user.name,
            "role": user.role.value,
            "business_name": user.business_name,
            "vehicle_types": user.vehicle_types,
            "operating_states": user.operating_states,
            "city": user.city,
            "village": user.village,
            "district": user.district,
            "state": user.state,
            "pincode": user.pincode,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    
    async def update_user(
        self, 
        db: AsyncSession,
        mobile_number: str, 
        user_type: str, 
        **updates
    ) -> Tuple[bool, str]:
        """Update user profile"""
        stmt = select(User).where(User.phone == mobile_number)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return False, "User not found"
        
        # Update allowed fields
        if 'name' in updates:
            user.name = updates['name']
        if 'business_name' in updates:
            user.business_name = updates['business_name']
        if 'vehicle_types' in updates:
            user.vehicle_types = updates['vehicle_types']
        if 'operating_states' in updates:
            user.operating_states = updates['operating_states']
        if 'city' in updates:
            user.city = updates['city']
        if 'village' in updates:
            user.village = updates['village']
        if 'state' in updates:
            user.state = updates['state']
        if 'district' in updates:
            user.district = updates['district']
        if 'pincode' in updates:
            user.pin.scalar_one_or_none()
        
        if not user:
            return False, "User not found"
        
        # Update allowed fields
        if 'name' in updates:
            user.name = updates['name']
        if 'city' in updates or 'village' in updates:
            user.village = updates.get('city') or updates.get('village')
        if 'state' in updates:
            user.state = updates['state']
        if 'district' in updates:
            user.district = updates['district']
        if 'pincode' in updates:
            user.pincode = updates['pincode']
        
        await db.commit()
        return True, "Profile updated successfully"
    
    async def logout(
        self, 
        db: AsyncSession,
        token: str
    ) -> bool:
        """Invalidate token (logout)"""
        stmt = select(AuthToken).where(AuthToken.token == token)
        result = await db.execute(stmt)
        token_record = result.scalar_one_or_none()
        
        if not token_record:
            return False
        
        token_record.is_active = False
        await db.commit()
        return True
    
    async def get_all_users_by_type(
        self, 
        db: AsyncSession,
        user_type: str
    ) -> list:
        """Get all users of a specific type"""
        role = self._map_user_type_to_role(user_type)
        
        stmt = select(User).where(User.role == role)
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        return [
            {
                "id": user.id,
                "mobile_number": user.phone,
                "user_type": user.role.value,
                "name": user.name,
                "role": user.role.value,
                "business_name": user.business_name,
                "vehicle_types": user.vehicle_types,
                "operating_states": user.operating_states,
                "city":user.city,
                "village": user.village,
                "district": user.district,
                "state": user.state,
                "pincode": user.pincode,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            for user in users
        ]
        
        return [
            {
                "id": user.id,
                "mobile_number": user.phone,
                "user_type": user.role.value,
                "name": user.name,
                "role": user.role.value,
                "village": user.village,
                "district": user.district,
                "state": user.state,
                "is_active": user.is_active
            }
            for user in users
        ]
