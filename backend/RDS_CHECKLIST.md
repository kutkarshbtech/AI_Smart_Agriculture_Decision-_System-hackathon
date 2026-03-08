# RDS Setup Checklist

Use this checklist to enable local development access to your RDS instance.

## ☐ Step 1: Enable Public Access (5-10 minutes)

1. ☐ Go to: https://ap-south-1.console.aws.amazon.com/rds/home?region=ap-south-1#databases:
2. ☐ Click on: `swadesh-ai-db-dev`
3. ☐ Click: `Modify` button
4. ☐ Scroll to "Connectivity" section
5. ☐ Change `Public access` → **YES**
6. ☐ Scroll down → Click `Continue`
7. ☐ Select: **Apply immediately**
8. ☐ Click: `Modify DB instance`
9. ☐ Wait 5-10 minutes (grab a coffee ☕)

---

## ☐ Step 2: Configure Security Group (2 minutes)

1. ☐ Go to: https://ap-south-1.console.aws.amazon.com/ec2/home?region=ap-south-1#SecurityGroups:
2. ☐ Find security group: `sg-0f7c92d82babc9f5d`
3. ☐ Click: `Edit inbound rules`
4. ☐ Click: `Add rule`
5. ☐ Set:
   - Type: **PostgreSQL**
   - Port: **5432** (auto-filled)
   - Source: **My IP** (auto-detects your IP)
   - Description: `Local dev machine`
6. ☐ Click: `Save rules`

---

## ☐ Step 3: Create .env File (2 minutes)

1. ☐ Copy the template below
2. ☐ Create file: `backend/.env`
3. ☐ Paste the template
4. ☐ Replace `YOUR_PASSWORD` with your RDS master password
5. ☐ Replace `postgres` with your master username if different

### .env Template:
```bash
APP_NAME=SwadeshAI
APP_ENV=development
DEBUG=True
AWS_REGION=ap-south-1

# IMPORTANT: Replace YOUR_PASSWORD with your RDS master password
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@swadesh-ai-db-dev.cd6iq6e4m1jo.ap-south-1.rds.amazonaws.com:5432/swadesh_ai

JWT_SECRET_KEY=change-me-in-production
ALLOWED_ORIGINS=*
```

---

## ☐ Step 4: Initialize Database (1 minute)

1. ☐ Open PowerShell
2. ☐ Run:
   ```powershell
   cd "c:\Users\utkarsh.kumar13\OneDrive - Infosys Limited\Documents\SwadeshAI\SwadeshAI\backend"
   python init_db.py
   ```
3. ☐ Verify output shows: `✅ Database initialized successfully!`

---

## ☐ Step 5: Start Backend (1 minute)

```powershell
cd "c:\Users\utkarsh.kumar13\OneDrive - Infosys Limited\Documents\SwadeshAI\SwadeshAI\backend"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

☐ Visit: http://localhost:8000/docs

---

## ☐ Step 6: Test Authentication (5 minutes)

### 6.1 Register User
Open http://localhost:8000/docs → Try:

```json
POST /api/auth/register
{
  "mobile_number": "+919876543210",
  "user_type": "seller",
  "name": "Test Farmer",
  "city": "Mumbai",
  "state": "Maharashtra"
}
```

☐ Should return: `"success": true`

---

### 6.2 Request OTP
```json
POST /api/auth/login/request-otp
{
  "mobile_number": "+919876543210",
  "user_type": "seller"
}
```

☐ Check server terminal for: `[AUTH] OTP for +919876543210: 123456`
☐ Copy the 6-digit OTP code

---

### 6.3 Verify OTP
```json
POST /api/auth/login/verify-otp
{
  "mobile_number": "+919876543210",
  "user_type": "seller",
  "otp": "123456"
}
```

☐ Should return: `access_token` (long random string)
☐ Copy the token

---

### 6.4 Get Profile
```json
GET /api/auth/profile
Headers:
  Authorization: Bearer YOUR_ACCESS_TOKEN
```

☐ Should return your user profile

---

## ✅ Success Criteria

You're done when:
- ☐ `python init_db.py` completes without errors
- ☐ FastAPI server starts at http://localhost:8000
- ☐ You can register a user
- ☐ You receive OTP in logs
- ☐ OTP verification returns a token
- ☐ Profile endpoint works with the token

---

## 🚨 Common Issues

### "Connection refused"
- ☐ Wait 10 minutes after enabling public access
- ☐ Check security group has your IP
- ☐ Try running: `Test-NetConnection swadesh-ai-db-dev.cd6iq6e4m1jo.ap-south-1.rds.amazonaws.com -Port 5432`

### "Authentication failed"
- ☐ Double-check password (case-sensitive!)
- ☐ Check username (usually `postgres` or `admin`)
- ☐ No spaces in DATABASE_URL

### "Database does not exist"
- ☐ Change database name from `swadesh_ai` to `postgres` in DATABASE_URL
- ☐ Or create database manually:
  ```sql
  CREATE DATABASE swadesh_ai;
  ```

---

## 📞 Need Help?

Check detailed guide: [YOUR_RDS_SETUP.md](./YOUR_RDS_SETUP.md)

---

## Estimated Time: ~20 minutes total
