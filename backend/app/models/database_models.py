"""
SQLAlchemy ORM models for SwadeshAI.
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text,
    ForeignKey, Enum, JSON, Date
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


# ─── Enums ───────────────────────────────────────────────

class ProduceCategory(str, enum.Enum):
    FRUIT = "fruit"
    VEGETABLE = "vegetable"
    GRAIN = "grain"
    SPICE = "spice"
    PULSE = "pulse"
    OILSEED = "oilseed"


class QualityGrade(str, enum.Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"


class SpoilageRisk(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, enum.Enum):
    SPOILAGE_WARNING = "spoilage_warning"
    PRICE_DROP = "price_drop"
    PRICE_SURGE = "price_surge"
    STORAGE_FAILURE = "storage_failure"
    BUYER_MATCH = "buyer_match"
    WEATHER_ALERT = "weather_alert"


class UserRole(str, enum.Enum):
    BUYER = "buyer"
    SELLER = "seller"
    LOGISTIC = "logistic"
    ADMIN = "admin"  # For system administrators


# ─── User (Buyer/Seller/Logistic) ──────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False)

    # Common fields
    language = Column(String(10), default="hi")  # ISO 639-1
    city = Column(String(100))
    state = Column(String(50))
    pincode = Column(String(6))
    latitude = Column(Float)
    longitude = Column(Float)

    # Business/Organization details (for buyers and logistics)
    business_name = Column(String(200))

    # Logistic provider specific
    vehicle_types = Column(JSON)  # List of vehicle types
    operating_states = Column(JSON)  # List of states where they operate

    # Seller specific
    village = Column(String(100))
    district = Column(String(100))

    # Profile
    profile_image_url = Column(String(512))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    produce_batches = relationship("ProduceBatch", back_populates="farmer")
    alerts = relationship("Alert", back_populates="user")
    otp_verifications = relationship("OTPVerification", back_populates="user", cascade="all, delete-orphan")
    auth_tokens = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")


# ─── Authentication ─────────────────────────────────────

class OTPVerification(Base):
    """OTP codes for phone-based authentication."""
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    phone = Column(String(15), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)
    is_verified = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="otp_verifications")


class AuthToken(Base):
    """Authentication tokens for logged-in sessions."""
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    token_type = Column(String(20), default="bearer")
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="auth_tokens")


# ─── Produce / Crop ─────────────────────────────────────

class CropType(Base):
    """Master table of supported crops with shelf-life metadata."""
    __tablename__ = "crop_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name_en = Column(String(100), nullable=False)
    name_hi = Column(String(100))
    name_local = Column(String(100))
    category = Column(Enum(ProduceCategory), nullable=False)
    avg_shelf_life_days = Column(Integer)  # at ambient temperature
    optimal_temp_min = Column(Float)  # °C
    optimal_temp_max = Column(Float)
    optimal_humidity_min = Column(Float)  # %
    optimal_humidity_max = Column(Float)
    cold_storage_shelf_life_days = Column(Integer)
    mandi_code = Column(String(20))  # eNAM / Agmarknet commodity code
    image_url = Column(String(512))

    batches = relationship("ProduceBatch", back_populates="crop_type")


class ProduceBatch(Base):
    """A batch of produce a farmer wants to sell."""
    __tablename__ = "produce_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crop_type_id = Column(Integer, ForeignKey("crop_types.id"), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    harvest_date = Column(Date, nullable=False)
    storage_type = Column(String(50), default="ambient")  # ambient, cold, controlled
    storage_temp = Column(Float)  # current storage temperature °C
    storage_humidity = Column(Float)  # current storage humidity %
    location_lat = Column(Float)
    location_lng = Column(Float)
    image_urls = Column(JSON, default=[])  # list of S3 keys
    quality_grade = Column(Enum(QualityGrade))
    quality_score = Column(Float)  # 0-100
    spoilage_risk = Column(Enum(SpoilageRisk))
    spoilage_probability = Column(Float)  # 0-1
    estimated_shelf_life_days = Column(Integer)
    is_sold = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    farmer = relationship("User", back_populates="produce_batches")
    crop_type = relationship("CropType", back_populates="batches")
    price_recommendations = relationship("PriceRecommendation", back_populates="batch")
    transactions = relationship("Transaction", back_populates="batch")


# ─── Pricing ─────────────────────────────────────────────

class MarketPrice(Base):
    """Daily mandi price data (fetched from external APIs)."""
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crop_type_id = Column(Integer, ForeignKey("crop_types.id"), nullable=False)
    mandi_name = Column(String(150), nullable=False)
    state = Column(String(50))
    district = Column(String(100))
    min_price = Column(Float)  # ₹/quintal
    max_price = Column(Float)
    modal_price = Column(Float)  # most common trading price
    date = Column(Date, nullable=False)
    source = Column(String(50), default="agmarknet")
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())


class PriceRecommendation(Base):
    """AI-generated price recommendation for a produce batch."""
    __tablename__ = "price_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("produce_batches.id"), nullable=False)
    recommended_min_price = Column(Float, nullable=False)  # seller-protected floor
    recommended_max_price = Column(Float, nullable=False)  # ideal price
    predicted_market_price = Column(Float)
    confidence_score = Column(Float)  # 0-1
    factors = Column(JSON)  # explanation factors
    recommendation_text = Column(Text)  # human-readable explanation
    valid_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    batch = relationship("ProduceBatch", back_populates="price_recommendations")


# ─── Buyers & Transactions ──────────────────────────────

class Buyer(Base):
    """Local shops, retailers, and buyers."""
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    shop_name = Column(String(150))
    contact_phone = Column(String(15), nullable=False)
    contact_name = Column(String(100))
    address = Column(Text)
    district = Column(String(100))
    state = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)
    preferred_crops = Column(JSON, default=[])  # list of crop_type_ids
    max_quantity_kg = Column(Float)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Transaction(Base):
    """Records of farmer-buyer trades."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("produce_batches.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")  # pending, confirmed, completed, cancelled
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    batch = relationship("ProduceBatch", back_populates="transactions")


# ─── Alerts ──────────────────────────────────────────────

class Alert(Base):
    """Notifications and warnings sent to users."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_type = Column(Enum(AlertType), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="info")  # info, warning, critical
    is_read = Column(Boolean, default=False)
    alert_metadata = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="alerts")
