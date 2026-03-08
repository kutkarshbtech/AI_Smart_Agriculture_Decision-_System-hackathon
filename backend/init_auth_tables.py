"""
Initialize authentication tables for SwadeshAI
Connects to PostgreSQL and creates: users, otp_verifications, auth_tokens tables

Usage:
    python init_auth_tables.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.database_models import Base, User, OTPVerification, AuthToken

# Database connection string
DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/swadesh_ai"


async def create_tables():
    """Create authentication tables in the database."""
    print("🔗 Connecting to database...")
    print(f"📍 Database URL: {DATABASE_URL}")
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        print("\n🏗️  Creating tables...")
        async with engine.begin() as conn:
            # Create only the authentication-related tables
            # This will create: users, otp_verifications, auth_tokens
            await conn.run_sync(Base.metadata.create_all)
        
        print("\n✅ Successfully created authentication tables!")
        print("📋 Tables created:")
        print("   1. users")
        print("   2. otp_verifications")
        print("   3. auth_tokens")
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        raise
    finally:
        await engine.dispose()


async def verify_tables():
    """Verify that tables exist in the database."""
    print("\n🔍 Verifying tables...")
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('users', 'otp_verifications', 'auth_tokens')
                ORDER BY table_name
                """
            )
            tables = [row[0] for row in result]
            
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"   • {table}")
            
            return len(tables) == 3
            
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False
    finally:
        await engine.dispose()


async def main():
    """Main execution function."""
    print("=" * 60)
    print("SwadeshAI Authentication Tables Initialization")
    print("=" * 60)
    
    try:
        # Create tables
        await create_tables()
        
        # Verify tables
        success = await verify_tables()
        
        if success:
            print("\n✨ Database initialization complete!")
            print("🚀 You can now run the authentication service.")
        else:
            print("\n⚠️  Some tables may not have been created correctly.")
            print("   Please check the error messages above.")
            
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
