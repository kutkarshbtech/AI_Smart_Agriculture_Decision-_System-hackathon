# Authentication Tables Setup for SwadeshAI

This setup supports **three user types** for the SwadeshAI platform:

## 🎭 Three User Types

### 1. **Buyer** (`buyer`)
- Purchases agricultural produce
- Fields: `business_name`, `city`, `state`, `pincode`

### 2. **Seller** (`seller`)
- Sells agricultural produce (farmers/vendors)
- Fields: `village`, `district`, `state`, `pincode`

### 3. **Logistic Provider** (`logistic`)
- Provides transportation and logistics services
- Fields: `business_name`, `vehicle_types[]`, `operating_states[]`, `city`, `state`

---

## 📊 Database Tables

### Table 1: `users`
Stores all user information for buyers, sellers, and logistic providers.

**Key Fields:**
- `phone` - Unique mobile number (authentication identifier)
- `role` - User type: buyer, seller, or logistic
- `name` - User/business name
- `business_name` - For buyers and logistics (optional)
- `vehicle_types` - JSON array for logistics (e.g., `["truck", "tempo"]`)
- `operating_states` - JSON array for logistics (e.g., `["Maharashtra", "Karnataka"]`)
- `village`, `district` - For sellers
- `city`, `state`, `pincode` - Location fields
- `is_verified` - Phone verification status
- `last_login` - Last login timestamp

### Table 2: `otp_verifications`
Stores OTP codes for phone-based authentication.

**Key Fields:**
- `user_id` - Foreign key to users table
- `phone` - Mobile number
- `otp_code` - 6-digit OTP
- `is_verified` - Verification status
- `attempts` - Number of verification attempts
- `expires_at` - OTP expiration time

### Table 3: `auth_tokens`
Stores authentication tokens for active sessions.

**Key Fields:**
- `user_id` - Foreign key to users table
- `token` - JWT or session token
- `token_type` - Usually "bearer"
- `is_active` - Token validity status
- `expires_at` - Token expiration time
- `last_used_at` - Last time token was used

---

## 🚀 Setup Instructions

### Option 1: Using SQL Script
```powershell
# Navigate to backend directory
cd SwadeshAI\backend

# Connect to PostgreSQL and run the SQL script
psql -U user -d swadesh_ai -f init_auth_tables.sql
```

### Option 2: Using Python Script
```powershell
# Ensure virtual environment is activated
.venv\Scripts\Activate.ps1

# Navigate to backend directory
cd SwadeshAI\backend

# Run the initialization script
python init_auth_tables.py
```

---

## 📝 User Registration Flow

### 1. Buyer Registration Example
```json
{
  "mobile_number": "+919876543210",
  "user_type": "buyer",
  "name": "Ramesh Traders",
  "business_name": "Ramesh Wholesale Traders",
  "city": "Mumbai",
  "state": "Maharashtra",
  "pincode": "400001"
}
```

### 2. Seller Registration Example
```json
{
  "mobile_number": "+918765432109",
  "user_type": "seller",
  "name": "Suresh Kumar",
  "village": "Kelgaon",
  "district": "Nashik",
  "state": "Maharashtra",
  "pincode": "422003"
}
```

### 3. Logistic Provider Registration Example
```json
{
  "mobile_number": "+917654321098",
  "user_type": "logistic",
  "name": "Vijay Transport",
  "business_name": "Vijay Logistics Services",
  "vehicle_types": ["truck", "tempo", "mini-truck"],
  "operating_states": ["Maharashtra", "Gujarat", "Karnataka"],
  "city": "Pune",
  "state": "Maharashtra",
  "pincode": "411001"
}
```

---

## 🔐 Authentication Flow

1. **Register** → User registers with mobile number and user type
2. **Request OTP** → OTP sent to mobile number (stored in `otp_verifications`)
3. **Verify OTP** → User enters OTP to verify
4. **Login** → JWT token generated (stored in `auth_tokens`)
5. **Access** → User can access APIs using the token

---

## ✅ Verification

After running the initialization script, verify tables exist:

```sql
-- Check all three tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('users', 'otp_verifications', 'auth_tokens');

-- Check users table structure
\d users

-- Check enum values
SELECT enumlabel 
FROM pg_enum 
WHERE enumtypid = 'user_role'::regtype;
```

Expected enum values: `buyer`, `seller`, `logistic`, `admin`

---

## 🔧 Database Connection

Default connection string:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/swadesh_ai
```

Update in `.env` file or `config.py` as needed.

---

## 📦 Dependencies

Required Python packages (should already be in `requirements.txt`):
- `sqlalchemy` - ORM
- `asyncpg` - Async PostgreSQL driver
- `psycopg2-binary` - PostgreSQL adapter

---

## 🐛 Troubleshooting

### Issue: Role enum doesn't exist
```sql
-- Drop and recreate enum
DROP TYPE IF EXISTS user_role CASCADE;
CREATE TYPE user_role AS ENUM ('buyer', 'seller', 'logistic', 'admin');
```

### Issue: Tables already exist with old schema
```sql
-- Drop tables and recreate
DROP TABLE IF EXISTS auth_tokens CASCADE;
DROP TABLE IF EXISTS otp_verifications CASCADE;
DROP TABLE IF EXISTS users CASCADE;
-- Then run init_auth_tables.sql again
```

### Issue: Connection refused
- Ensure PostgreSQL is running: `Get-Service postgresql*`
- Check connection credentials in DATABASE_URL
- Verify database exists: `psql -U user -l`

---

## 📞 Support

For issues or questions:
1. Check database logs: `psql -U user -d swadesh_ai`
2. Verify table structures: `\d users`, `\d otp_verifications`, `\d auth_tokens`
3. Check enum types: `\dT user_role`
