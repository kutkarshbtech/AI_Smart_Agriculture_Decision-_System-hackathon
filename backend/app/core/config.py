"""
Application configuration using Pydantic Settings.
Loads from environment variables or .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    # App
    APP_NAME: str = "SwadeshAI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # AWS-Only Mode — disables all local/simulated fallbacks
    # When True, every inference MUST go through AWS services
    AWS_ONLY: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    # AWS Configuration
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # S3
    S3_BUCKET_NAME: str = "swadesh-ai-data"
    S3_PRODUCE_IMAGES_PREFIX: str = "produce-images/"

    # DynamoDB
    DYNAMODB_TABLE_FARMERS: str = "swadesh-farmers"
    DYNAMODB_TABLE_PRODUCE: str = "swadesh-produce"
    DYNAMODB_TABLE_TRANSACTIONS: str = "swadesh-transactions"

    # Database (SQLite for local dev, PostgreSQL for production)
    DATABASE_URL: str = "sqlite+aiosqlite:///./swadesh_ai.db"

    # Neptune (Knowledge Graph)
    NEPTUNE_ENDPOINT: str = ""
    NEPTUNE_PORT: int = 8182

    # SageMaker
    SAGEMAKER_SPOILAGE_ENDPOINT: str = "swadesh-spoilage-model"
    SAGEMAKER_PRICING_ENDPOINT: str = "swadesh-pricing-model"
    SAGEMAKER_FRESHNESS_ENDPOINT: str = "swadesh-ai-freshness-detector-endpoint"

    # Amazon Bedrock (LLM)
    BEDROCK_MODEL_ID: str = "amazon.nova-lite-v1:0"
    BEDROCK_REGION: str = "us-east-1"

    # Amazon Transcribe (Speech-to-Text)
    TRANSCRIBE_REGION: str = "ap-south-1"
    TRANSCRIBE_S3_BUCKET: str = "swadesh-ai-data-ap"
    TRANSCRIBE_S3_PREFIX: str = "voice-uploads/"

    # Amazon Polly (Text-to-Speech)
    POLLY_REGION: str = "us-east-1"

    # Amazon Rekognition
    REKOGNITION_COLLECTION_ID: str = "produce-quality"

    # External APIs
    WEATHER_API_KEY: str = ""
    WEATHER_API_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    MANDI_API_BASE_URL: str = "https://api.data.gov.in/resource"
    MANDI_API_KEY: str = ""

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Auth
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    # Location Service
    AWS_LOCATION_INDEX: str = "swadesh-place-index"
    AWS_LOCATION_ROUTE_CALCULATOR: str = "swadesh-route-calc"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
