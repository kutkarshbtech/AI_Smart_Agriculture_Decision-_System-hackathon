"""
Database initialization script for SwadeshAI PostgreSQL.
Creates all tables for authentication and application use.

Run this script after setting up your AWS RDS PostgreSQL instance.

Usage:
    python init_db.py
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models.database_models import Base


async def init_database():
    """Initialize database tables"""
    print("🔧 Initializing SwadeshAI PostgreSQL Database...")
    print(f"📍 Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    
    try:
        # Create async engine
        engine = create_async_engine(settings.DATABASE_URL, echo=True)
        
        # Create all tables
        async with engine.begin() as conn:
            print("\n🗄️  Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
        
        await engine.dispose()
        
        print("\n✅ Database initialized successfully!")
        print("\n📋 Created tables:")
        print("   1. users - User accounts (farmers, buyers, FPO, admin)")
        print("   2. otp_verifications - OTP codes for authentication")
        print("   3. auth_tokens - Session tokens for logged-in users")
        print("   4. crop_types - Master list of supported crops")
        print("   5. produce_batches - Farmer produce listings")
        print("   6. market_prices - Mandi price data")
        print("   7. price_recommendations - AI pricing recommendations")
        print("   8. buyers - Buyer/retailer information")
        print("   9. transactions - Trade records")
        print("  10. alerts - User notifications")
        
        print("\n🎯 Next steps:")
        print("   1. Update .env with your RDS endpoint:")
        print("      DATABASE_URL=postgresql+asyncpg://username:password@your-rds-endpoint:5432/swadesh_ai")
        print("   2. Start the FastAPI server: uvicorn app.main:app --reload")
        print("   3. Test authentication: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        print("\n🔍 Troubleshooting:")
        print("   1. Check DATABASE_URL in .env file")
        print("   2. Ensure RDS security group allows your IP")
        print("   3. Verify database credentials")
        print("   4. Check if PostgreSQL is running")
        sys.exit(1)


async def seed_crop_types():
    """Seed initial crop types"""
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    from app.models.database_models import CropType, ProduceCategory
    
    print("\n🌾 Seeding crop types...")
    
    crops = [
        {"name_en": "Tomato", "name_hi": "टमाटर", "category": ProduceCategory.VEGETABLE, "avg_shelf_life_days": 7},
        {"name_en": "Potato", "name_hi": "आलू", "category": ProduceCategory.VEGETABLE, "avg_shelf_life_days": 30},
        {"name_en": "Onion", "name_hi": "प्याज", "category": ProduceCategory.VEGETABLE, "avg_shelf_life_days": 60},
        {"name_en": "Rice", "name_hi": "चावल", "category": ProduceCategory.GRAIN, "avg_shelf_life_days": 365},
        {"name_en": "Wheat", "name_hi": "गेहूं", "category": ProduceCategory.GRAIN, "avg_shelf_life_days": 365},
        {"name_en": "Mango", "name_hi": "आम", "category": ProduceCategory.FRUIT, "avg_shelf_life_days": 5},
        {"name_en": "Banana", "name_hi": "केला", "category": ProduceCategory.FRUIT, "avg_shelf_life_days": 7},
        {"name_en": "Apple", "name_hi": "सेब", "category": ProduceCategory.FRUIT, "avg_shelf_life_days": 30},
        {"name_en": "Cauliflower", "name_hi": "फूलगोभी", "category": ProduceCategory.VEGETABLE, "avg_shelf_life_days": 7},
        {"name_en": "Spinach", "name_hi": "पालक", "category": ProduceCategory.LEAFY_GREEN, "avg_shelf_life_days": 3},
        {"name_en": "Okra", "name_hi": "भिंडी", "category": ProduceCategory.VEGETABLE, "avg_shelf_life_days": 5},
        {"name_en": "Brinjal", "name_hi": "बैंगन", "category": ProduceCategory.VEGETABLE, "avg_shelf_life_days": 7},
        {"name_en": "Green Chili", "name_hi": "हरी मिर्च", "category": ProduceCategory.SPICE, "avg_shelf_life_days": 7},
        {"name_en": "Grapes", "name_hi": "अंगूर", "category": ProduceCategory.FRUIT, "avg_shelf_life_days": 7},
        {"name_en": "Pomegranate", "name_hi": "अनार", "category": ProduceCategory.FRUIT, "avg_shelf_life_days": 30},
        {"name_en": "Guava", "name_hi": "अमरूद", "category": ProduceCategory.FRUIT, "avg_shelf_life_days": 7},
    ]
    
    try:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Check if crops already exist
            from sqlalchemy import select
            stmt = select(CropType).limit(1)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                print("   ⏭️  Crops already seeded, skipping...")
                return
            
            # Add crops
            for crop_data in crops:
                crop = CropType(**crop_data)
                session.add(crop)
            
            await session.commit()
            print(f"   ✅ Seeded {len(crops)} crop types")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"   ⚠️  Seeding failed (not critical): {e}")


async def main():
    """Main execution"""
    await init_database()
    await seed_crop_types()


if __name__ == "__main__":
    asyncio.run(main())
