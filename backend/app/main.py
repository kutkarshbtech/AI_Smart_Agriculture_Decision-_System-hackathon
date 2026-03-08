"""
SwadeshAI Backend - FastAPI Application
AI-powered post-harvest decision intelligence for Indian farmers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import (
    health,
    produce,
    pricing,
    spoilage,
    quality,
    buyers,
    alerts,
    chatbot,
    dashboard,
    tts,
    weather,
    causal,
    logistics,
)
from app.api.routes import auth as auth_routes
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: Load ML models, init connections, create DB tables
    print("🚀 SwadeshAI Backend starting up...")
    from app.core.database import init_db
    await init_db()
    print("✅ Database tables ready")
    yield
    # Shutdown: Cleanup
    print("🛑 SwadeshAI Backend shutting down...")


app = FastAPI(
    title="SwadeshAI API",
    description="AI-powered post-harvest decision intelligence for Indian farmers",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(health.router, tags=["Health"])
app.include_router(produce.router, prefix="/api/v1/produce", tags=["Produce"])
app.include_router(pricing.router, prefix="/api/v1/pricing", tags=["Pricing"])
app.include_router(spoilage.router, prefix="/api/v1/spoilage", tags=["Spoilage"])
app.include_router(quality.router, prefix="/api/v1/quality", tags=["Quality Assessment"])
app.include_router(buyers.router, prefix="/api/v1/buyers", tags=["Buyer Matching"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["AI Chatbot"])
app.include_router(tts.router, prefix="/api/v1/tts", tags=["Text-to-Speech"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(weather.router, prefix="/api/v1/weather", tags=["Weather"])
app.include_router(causal.router, prefix="/api/v1/causal", tags=["Causal Inference"])
app.include_router(logistics.router, prefix="/api/v1/logistics", tags=["Logistics"])
app.include_router(auth_routes.router, tags=["Authentication"])
