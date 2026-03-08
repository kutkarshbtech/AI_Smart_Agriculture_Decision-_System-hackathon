# Your RDS PostgreSQL Setup - Step-by-Step Guide

## ✅ RDS Instance Created Successfully!

**Endpoint:** `swadesh-ai-db-dev.cd6iq6e4m1jo.ap-south-1.rds.amazonaws.com`  
**Port:** `5432`  
**Region:** `ap-south-1a`  
**VPC:** `swadesh-ai-vpc-dev (vpc-0d362fbc6ef6c6f9d)`  
**Security Group:** `sg-0f7c92d82babc9f5d`

---

## 🔴 **CRITICAL ISSUE: Public Access is Disabled**

**Current Status:** `Publicly accessible: No`

This means you **cannot connect from your local machine**. The database is only accessible from within the AWS VPC.

---

## 🚀 Quick Fix (Enables Local Development)

### Step 1: Enable Public Access

1. **Go to AWS RDS Console** → [RDS Databases](https://ap-south-1.console.aws.amazon.com/rds/home?region=ap-south-1#databases:)
2. **Select** `swadesh-ai-db-dev`
3. **Click** `Modify` button (top right)
4. **Scroll to "Connectivity"** section
5. **Under "Additional configuration"** → Change `Public access` to **YES**
6. **Scroll to bottom** → Click `Continue`
7. **Apply immediately** → Check this option
8. **Click** `Modify DB instance`
9. **Wait 5-10 minutes** for changes to apply

### Step 2: Configure Security Group

1. **Go to EC2 Console** → [Security Groups](https://ap-south-1.console.aws.amazon.com/ec2/home?region=ap-south-1#SecurityGroups:)
2. **Find and select:** `sg-0f7c92d82babc9f5d` (swadesh-ai-dev-DBSecurityGroup)
3. **Click** `Edit inbound rules`
4. **Click** `Add rule`
5. **Configure:**
   - **Type:** `PostgreSQL`
   - **Protocol:** `TCP` (auto-filled)
   - **Port Range:** `5432` (auto-filled)
   - **Source:** `My IP` (automatically detects your IP)
   - **Description:** `My local development machine`
6. **Click** `Save rules`

---

## 📝 Step 3: Create .env File

Create a new file: `backend/.env`

```bash
# Application Settings
APP_NAME=SwadeshAI
APP_ENV=development
DEBUG=True
HOST=0.0.0.0
PORT=8000
AWS_ONLY=False

# AWS Credentials
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here

# PostgreSQL Database - YOUR SPECIFIC RDS INSTANCE
# Replace 'postgres' with your master username if different
# Replace 'your_master_password' with your RDS master password
# Replace 'swadesh_ai' with your database name if different
DATABASE_URL=postgresql+asyncpg://postgres:your_master_password@swadesh-ai-db-dev.cd6iq6e4m1jo.ap-south-1.rds.amazonaws.com:5432/swadesh_ai

# External APIs (Optional)
WEATHER_API_KEY=your_openweathermap_key
MANDI_API_KEY=your_data_gov_in_key

# JWT Secret
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# CORS
ALLOWED_ORIGINS=*
```

**Important:** Replace these values:
- `postgres` → Your RDS master username (check RDS console if unsure)
- `your_master_password` → The password you set during RDS creation
- `swadesh_ai` → Your database name (default is usually `postgres`, change if needed)

---

## 🗄️ Step 4: Initialize Database

After public access is enabled and security group is configured:

```powershell
cd backend
python init_db.py
```

**Expected Output:**
```
🔧 Initializing SwadeshAI PostgreSQL Database...
📍 Database URL: swadesh-ai-db-dev.cd6iq6e4m1jo.ap-south-1.rds.amazonaws.com:5432

🗄️  Creating tables...
✅ Database initialized successfully!

📋 Created tables:
   1. users - User accounts
   2. otp_verifications - OTP codes
   3. auth_tokens - Session tokens
   ... (10 tables total)

🌾 Seeding crop types...
   ✅ Seeded 16 crop types
```

---

## 🧪 Step 5: Test Connection

### Option 1: Using psql CLI
```powershell
psql -h swadesh-ai-db-dev.cd6iq6e4m1jo.ap-south-1.rds.amazonaws.com -U postgres -d swadesh_ai -p 5432
# Enter password when prompted
```

### Option 2: Using Python
```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def test():
    url = "postgresql+asyncpg://postgres:YOUR_PASSWORD@swadesh-ai-db-dev.cd6iq6e4m1jo.ap-south-1.rds.amazonaws.com:5432/swadesh_ai"
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        result = await conn.execute("SELECT version();")
        print(await result.fetchone())
    await engine.dispose()

asyncio.run(test())
```

---

## 🚀 Step 6: Start Backend

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000/docs

---

## 📊 Test Authentication Flow

### 1. Register User
```bash
curl -X POST "http://localhost:8000/api/auth/register" ^
  -H "Content-Type: application/json" ^
  -d "{\"mobile_number\": \"+919876543210\", \"user_type\": \"seller\", \"name\": \"Test Farmer\", \"city\": \"Mumbai\", \"state\": \"Maharashtra\"}"
```

### 2. Request OTP
```bash
curl -X POST "http://localhost:8000/api/auth/login/request-otp" ^
  -H "Content-Type: application/json" ^
  -d "{\"mobile_number\": \"+919876543210\", \"user_type\": \"seller\"}"
```

Check server logs for OTP (e.g., `[AUTH] OTP for +919876543210: 123456`)

### 3. Verify OTP
```bash
curl -X POST "http://localhost:8000/api/auth/login/verify-otp" ^
  -H "Content-Type: application/json" ^
  -d "{\"mobile_number\": \"+919876543210\", \"user_type\": \"seller\", \"otp\": \"123456\"}"
```

Returns JWT token!

---

## ⚠️ Troubleshooting

### Error: "Connection refused" or "Connection timeout"
- ✅ **Check:** Public access is enabled (wait 5-10 minutes after enabling)
- ✅ **Check:** Security group has inbound rule for port 5432 from your IP
- ✅ **Check:** Your firewall allows outbound connections to port 5432

### Error: "Authentication failed for user"
- ✅ **Check:** Master username is correct (usually `postgres` or `admin`)
- ✅ **Check:** Password is correct (no typos)
- ✅ **Check:** You're using the master user credentials

### Error: "Database does not exist"
- ✅ **Check:** Database name in connection string matches actual database
- ✅ **Default:** RDS creates a database with the name you specified during setup
- ✅ **If needed:** Connect to `postgres` database first and create `swadesh_ai`:
  ```sql
  CREATE DATABASE swadesh_ai;
  ```

### Error: "SSL connection required"
- **Option 1:** Add `?ssl=require` to connection string
  ```
  DATABASE_URL=postgresql+asyncpg://...?ssl=require
  ```
- **Option 2:** Disable SSL requirement in RDS parameter group (not recommended)

---

## 🔐 Security Best Practices (After Testing)

Once testing is complete:

1. **Disable Public Access** (for production)
2. **Deploy Backend to AWS**:
   - ECS Fargate in same VPC
   - EC2 instance in same VPC
   - Lambda functions with VPC configuration
3. **Use IAM Authentication** instead of password
4. **Enable SSL/TLS** for database connections
5. **Rotate Credentials** regularly
6. **Use Secrets Manager** for storing credentials

---

## 📞 Quick Reference

| Item | Value |
|------|-------|
| **Endpoint** | `swadesh-ai-db-dev.cd6iq6e4m1jo.ap-south-1.rds.amazonaws.com` |
| **Port** | `5432` |
| **Region** | `ap-south-1` |
| **VPC** | `vpc-0d362fbc6ef6c6f9d` |
| **Security Group** | `sg-0f7c92d82babc9f5d` |
| **Availability Zone** | `ap-south-1a` |

---

## Next Steps After Database is Working

1. ✅ Test authentication endpoints (register, login, verify OTP)
2. ✅ Configure AWS SNS for production SMS delivery
3. ✅ Set up S3 bucket for image uploads
4. ✅ Deploy backend to AWS ECS/Fargate
5. ✅ Set up CloudWatch monitoring
6. ✅ Configure auto-scaling policies

---

Good luck! Let me know if you encounter any issues. 🚀
