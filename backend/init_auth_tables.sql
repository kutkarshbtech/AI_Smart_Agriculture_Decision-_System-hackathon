-- SwadeshAI Authentication Tables
-- Database: swadesh_ai
-- Connection: postgresql://user:password@localhost:5432/swadesh_ai

-- ============================================================================
-- ENUMS
-- ============================================================================

-- User Role Enum for three user types: buyer, seller, logistic
CREATE TYPE user_role AS ENUM ('buyer', 'seller', 'logistic', 'admin');

-- ============================================================================
-- TABLE 1: users (supports buyer, seller, logistic)
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    role user_role NOT NULL,
    
    -- Common fields
    language VARCHAR(10) DEFAULT 'hi',
    city VARCHAR(100),
    state VARCHAR(50),
    pincode VARCHAR(6),
    latitude FLOAT,
    longitude FLOAT,
    
    -- Business/Organization details (for buyers and logistics)
    business_name VARCHAR(200),
    
    -- Logistic provider specific (JSON arrays)
    vehicle_types JSONB,
    operating_states JSONB,
    
    -- Seller specific
    village VARCHAR(100),
    district VARCHAR(100),
    
    -- Profile and status
    profile_image_url VARCHAR(512),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create index on phone for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);

-- ============================================================================
-- TABLE 2: otp_verifications
-- ============================================================================

CREATE TABLE IF NOT EXISTS otp_verifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    phone VARCHAR(15) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    attempts INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on phone for faster OTP lookups
CREATE INDEX IF NOT EXISTS idx_otp_phone ON otp_verifications(phone);

-- ============================================================================
-- TABLE 3: auth_tokens
-- ============================================================================

CREATE TABLE IF NOT EXISTS auth_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token VARCHAR(255) UNIQUE NOT NULL,
    token_type VARCHAR(20) DEFAULT 'bearer',
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on token for faster authentication
CREATE INDEX IF NOT EXISTS idx_auth_tokens_token ON auth_tokens(token);

-- ============================================================================
-- TRIGGER: Update updated_at on users table
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify tables created successfully
SELECT 
    table_name, 
    table_type
FROM 
    information_schema.tables
WHERE 
    table_schema = 'public' 
    AND table_name IN ('users', 'otp_verifications', 'auth_tokens')
ORDER BY 
    table_name;

-- Display table structure
\d users
\d otp_verifications
\d auth_tokens
