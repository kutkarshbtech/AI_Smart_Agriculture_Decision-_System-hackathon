# AWS RDS PostgreSQL Setup for SwadeshAI Authentication

## Overview

SwadeshAI now uses **AWS RDS PostgreSQL** for authentication instead of file-based storage. This provides:
- ✅ Production-ready user management
- ✅ Secure OTP verification storage
- ✅ Session token management
- ✅ ACID transaction support

## Three Database Tables

### 1. **users** - User Registration Data
```sql
id, phone (unique), name, role (FARMER/BUYER/FPO/ADMIN)
village, district, state, latitude, longitude
pin_code, profile_image_url, is_active
created_at, updated_at
```

### 2. **otp_verifications** - OTP Codes
```sql
id, user_id (FK), phone, otp_code
is_verified, attempts, expires_at
created_at
```

### 3. **auth_tokens** - Session Tokens
```sql
id, user_id (FK), token (unique), token_type
is_active, expires_at, last_used_at
created_at
```

## AWS RDS Setup Steps

### Step 1: Create RDS PostgreSQL Instance

1. **Go to AWS RDS Console** (Mumbai region: `ap-south-1`)
2. **Click "Create database"**
3. **Configuration:**
   - **Engine**: PostgreSQL 15.x or higher
   - **Templates**: Free tier or Dev/Test
   - **Instance class**: 
     - Free tier: `db.t3.micro`
     - Production: `db.t3.small` or higher
   - **Storage**: 20GB General Purpose SSD (gp3)
   - **DB instance identifier**: `swadesh-ai-db`
   - **Master username**: `swadesh_admin` (or your choice)
   - **Master password**: Create strong password (save this!)
   - **Database name**: `swadesh_ai`

4. **Connectivity:**
   - **Public access**: YES (for development)
   - **VPC security group**: Create new → open port 5432
   - **Availability zone**: No preference

5. **Additional configuration:**
   - **Initial database name**: `swadesh_ai`
   - **Backup**: 7 days retention
   - **Monitoring**: Enable Enhanced Monitoring

6. **Click "Create database"** (takes 5-10 minutes)

### Step 2: Configure Security Group

1. **Go to RDS instance details** → Click on VPC security group
2. **Edit inbound rules:**
   - Type: `PostgreSQL`
   - Protocol: `TCP`
   - Port: `5432`
   - Source: `My IP` (or `0.0.0.0/0` for testing - **NOT recommended for production**)
3. **Save rules**

### Step 3: Get RDS Endpoint

1. **Go to RDS Console** → Click on your instance
2. **Copy the endpoint** (looks like: `swadesh-ai-db.abc123.ap-south-1.rds.amazonaws.com`)
3. **Note the port**: 5432

### Step 4: Update Environment Configuration

Create `backend/.env` file with:

```bash
# PostgreSQL Database (AWS RDS)
DATABASE_URL=postgresql+asyncpg://swadesh_admin:YOUR_PASSWORD@swadesh-ai-db.abc123.ap-south-1.rds.amazonaws.com:5432/swadesh_ai

# AWS Credentials (for SNS SMS delivery)
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Other settings (optional - has fallbacks)
WEATHER_API_KEY=your_openweathermap_key
MANDI_API_KEY=your_data_gov_in_key
```

**Replace:**
- `YOUR_PASSWORD` → Your RDS master password
- `swadesh-ai-db.abc123` → Your actual RDS endpoint
- `your_access_key` → Your AWS IAM access key
- `your_secret_key` → Your AWS IAM secret key

### Step 5: Initialize Database

```bash
cd backend
python init_db.py
```

**Expected output:**
```
🔧 Initializing SwadeshAI PostgreSQL Database...
📍 Database URL: swadesh-ai-db.xyz.ap-south-1.rds.amazonaws.com:5432

🗄️  Creating tables...
✅ Database initialized successfully!

📋 Created tables:
   1. users - User accounts
   2. otp_verifications - OTP codes
   3. auth_tokens - Session tokens
   4. crop_types - Supported crops
   5. produce_batches - Farmer listings
   ... (10 tables total)

🌾 Seeding crop types...
   ✅ Seeded 16 crop types
```

### Step 6: Test Connection

**Option 1: Using Python**
```python
from sqlalchemy import create_engine
url = "postgresql://swadesh_admin:password@your-endpoint:5432/swadesh_ai"
engine = create_engine(url)
with engine.connect() as conn:
    result = conn.execute("SELECT version();")
    print(result.fetchone())
```

**Option 2: Using psql CLI**
```bash
psql -h swadesh-ai-db.abc123.ap-south-1.rds.amazonaws.com -U swadesh_admin -d swadesh_ai
# Enter password when prompted
```

### Step 7: Start Application

```bash
# Activate virtual environment
cd backend
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\Activate.ps1  # Windows

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000/docs

## Testing Authentication

### 1. Register User
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "mobile_number": "+919876543210",
    "user_type": "seller",
    "name": "Test Farmer",
    "city": "Mumbai",
    "state": "Maharashtra"
  }'
```

### 2. Request OTP
```bash
curl -X POST "http://localhost:8000/api/auth/login/request-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "mobile_number": "+919876543210",
    "user_type": "seller"
  }'
```

**Response includes demo OTP** (also printed in server logs)

### 3. Verify OTP
```bash
curl -X POST "http://localhost:8000/api/auth/login/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "mobile_number": "+919876543210",
    "user_type": "seller",
    "otp": "123456"
  }'
```

**Returns:** `access_token` (use in Authorization header)

### 4. Get Profile
```bash
curl -X GET "http://localhost:8000/api/auth/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## AWS Services Summary

| Service | Purpose | When Needed |
|---------|---------|-------------|
| **RDS PostgreSQL** | User accounts, OTP, tokens | ✅ REQUIRED for auth |
| **Amazon SNS** | SMS OTP delivery | Optional (demo prints OTP) |
| **S3** | Image storage | Optional (local fallback) |
| **Rekognition** | Quality assessment | Optional (local fallback) |
| **Bedrock** | AI chatbot | Optional (rule-based fallback) |
| **SageMaker** | ML models | Optional (local models) |

## Troubleshooting

### Error: "Connection refused"
- ✅ Check RDS security group allows your IP
- ✅ Verify RDS endpoint in DATABASE_URL
- ✅ Ensure RDS status is "Available"

### Error: "Authentication failed"
- ✅ Verify master password in DATABASE_URL
- ✅ Check username is correct (`swadesh_admin`)

### Error: "Database does not exist"
- ✅ Ensure you set "Initial database name" during RDS creation
- ✅ Or create database manually: `CREATE DATABASE swadesh_ai;`

### Error: "SSL required"
- Update DATABASE_URL to include SSL:
  ```
  postgresql+asyncpg://user:pass@endpoint:5432/db?ssl=require
  ```

## Cost Estimation

**Free Tier (12 months):**
- RDS db.t3.micro: 750 hours/month FREE
- Storage: 20GB FREE
- **Estimated cost after free tier: ~₹1,500/month**

**Production:**
- RDS db.t3.small: ~₹2,000/month
- Storage 50GB: ~₹350/month
- Backups: ~₹200/month
- **Total: ~₹2,550/month**

## Next Steps

After RDS setup:
1. ✅ Configure AWS SNS for production OTP delivery
2. ✅ Set up S3 bucket for image uploads
3. ✅ Deploy FastAPI to ECS Fargate
4. ✅ Set up CloudWatch monitoring
5. ✅ Configure auto-scaling

## Support

For issues:
1. Check [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
2. Review backend logs: `tail -f backend/app.log`
3. Test database connection: `python backend/init_db.py`
