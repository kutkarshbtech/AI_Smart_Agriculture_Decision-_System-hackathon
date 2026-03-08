# SwadeshAI Authentication System

Complete mobile number + OTP authentication for Buyers, Sellers, and Logistic Providers.

## Features

- 📱 **Mobile OTP Authentication** - Secure login with 6-digit OTP
- 👥 **Three User Types** - Buyer, Seller, Logistic Provider
- 🔐 **Session Management** - Token-based authentication with 24-hour expiry
- 💾 **File-based Storage** - Demo-ready authentication without database
- 🚀 **Dual Platform** - Works in both Streamlit and React frontend

## Architecture

```
SwadeshAI/
├── backend/
│   ├── app/
│   │   ├── schemas/
│   │   │   └── auth.py                 # Pydantic schemas for auth
│   │   ├── services/
│   │   │   └── auth_service.py         # Core authentication logic
│   │   └── api/
│   │       └── routes/
│   │           └── auth.py             # FastAPI endpoints
│   └── streamlit_auth.py               # Streamlit authentication UI
├── frontend/
│   └── src/
│       ├── context/
│       │   └── AuthContext.jsx         # React auth context
│       └── components/
│           ├── Login.jsx               # Login component
│           └── Register.jsx            # Registration component
└── data/
    └── auth/                           # Auth data storage
        ├── users.json                  # User database
        ├── otp_store.json              # Active OTPs
        └── tokens.json                 # Session tokens
```

## User Types

### 1. 🛒 Buyer (Wholesaler/Retailer)
- Access to quality assessment
- Find sellers with quality produce
- View mandi prices
- Logistics recommendations

### 2. 🌾 Seller (Farmer/Supplier)
- Upload produce photos for AI quality check
- Get price recommendations
- Find buyers
- Compare mandi prices

### 3. 🚚 Logistic Provider
- Connect with buyers and sellers
- Manage vehicle fleet
- Route optimization
- View transport opportunities

## Usage

### Streamlit (Integrated)

The authentication is automatically integrated in `demo_quality_price.py`:

```bash
cd SwadeshAI
.\.venv\Scripts\streamlit.exe run backend\demo_quality_price.py --server.port 8529
```

**What happens:**
1. App checks if user is authenticated
2. If not, shows Login/Register tabs
3. After successful login, shows full app with user info in sidebar
4. Logout button available in sidebar

**Demo Flow:**
1. **Register** - Enter mobile (+919876543210), select type, fill details
2. **Login** - Enter mobile, request OTP
3. **OTP** - Displayed on screen for demo (in production, sent via SMS)
4. **Access** - Full app features unlocked

### Standalone Auth App

Test authentication independently:

```bash
cd SwadeshAI
.\.venv\Scripts\streamlit.exe run backend\streamlit_auth.py
```

### React Frontend

```bash
cd frontend
npm install         # Install dependencies
npm run dev         # Start dev server on port 3000
```

**Routes:**
- `/login` - Login page
- `/register` - Registration page
- `/` - Protected: Quality Assessment (requires login)
- `/mandi-prices` - Protected: Mandi Prices
- `/find-buyers` - Protected: Buyer Matching
- `/about` - Protected: About Page

**Demo Flow:**
1. Open http://localhost:3000
2. Automatically redirected to `/login`
3. Register or login with mobile + OTP
4. Redirected to main app
5. User info shown in header with logout button

## API Endpoints

### POST `/api/auth/register`
Register new user

**Request:**
```json
{
  "mobile_number": "+919876543210",
  "user_type": "buyer",
  "name": "Rajesh Kumar",
  "business_name": "Kumar Traders",
  "city": "Delhi",
  "state": "Delhi",
  "pincode": "110001"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "mobile_number": "+919876543210",
    "user_type": "buyer",
    "name": "Rajesh Kumar"
  }
}
```

### POST `/api/auth/login/request-otp`
Request OTP for login

**Request:**
```json
{
  "mobile_number": "+919876543210",
  "user_type": "buyer"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "otp_sent": true,
  "demo_otp": "123456"
}
```

### POST `/api/auth/login/verify-otp`
Verify OTP and login

**Request:**
```json
{
  "mobile_number": "+919876543210",
  "user_type": "buyer",
  "otp": "123456"
}
```

**Response:**
```json
{
  "access_token": "aBc123XyZ...",
  "token_type": "bearer",
  "user_id": 1,
  "user_type": "buyer",
  "name": "Rajesh Kumar",
  "mobile_number": "+919876543210"
}
```

### GET `/api/auth/profile`
Get user profile (requires auth token)

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "mobile_number": "+919876543210",
  "user_type": "buyer",
  "name": "Rajesh Kumar",
  "business_name": "Kumar Traders",
  "city": "Delhi",
  "state": "Delhi",
  "is_active": true,
  "is_verified": true,
  "created_at": "2026-03-07T14:30:00",
  "last_login": "2026-03-07T14:35:00"
}
```

### POST `/api/auth/logout`
Logout (invalidate token)

**Headers:**
```
Authorization: Bearer <token>
```

## Authentication Flow

```
┌─────────────┐
│   Register  │  Fill form with mobile + details
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ User stored │  data/auth/users.json
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Login    │  Enter mobile number
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Request OTP │  Generate 6-digit OTP
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ OTP stored  │  data/auth/otp_store.json (5-min expiry)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Verify OTP  │  User enters OTP
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Generate Token│ 32-byte secure token
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Token stored │  data/auth/tokens.json (24-hour expiry)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Authenticated│ Access full app features
└─────────────┘
```

## Security Features

1. **OTP Expiry** - 5 minutes
2. **Max Attempts** - 3 tries per OTP
3. **Token Expiry** - 24 hours
4. **Secure Token** - 32-byte URL-safe token
5. **Mobile Validation** - Regex validation for phone numbers
6. **Protected Routes** - Authentication required for app features

## Demo Mode

**OTP Display:**
- In demo mode, OTP is displayed on screen
- Console also prints OTP: `[AUTH] OTP for +919876543210: 123456`
- In production, integrate SMS service (Twilio, AWS SNS, etc.)

**Sample Users:**
```
Buyer: +919876543210
Seller: +919876543211
Logistic: +919876543212
```

## Production Deployment

### 1. SMS Integration
Replace OTP display with SMS service:

```python
# In auth_service.py -> send_otp()
import boto3

sns = boto3.client('sns', region_name='ap-south-1')
sns.publish(
    PhoneNumber=mobile_number,
    Message=f'Your SwadeshAI OTP is: {otp}. Valid for 5 minutes.'
)
```

### 2. Database Storage
Replace file storage with PostgreSQL/MongoDB:

```python
# Replace _load_json/_save_json with SQLAlchemy/PyMongo
from sqlalchemy import create_engine
from models import User, OTPStore, Token
```

### 3. Environment Variables
```bash
# .env
JWT_SECRET_KEY=your-secret-key
SMS_SERVICE_KEY=your-twilio-key
DATABASE_URL=postgresql://user:pass@localhost/swadesh
```

### 4. Rate Limiting
Add rate limiting to prevent OTP spam:

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/login/request-otp")
@limiter.limit("3/minute")
async def request_otp(request: Request, ...):
    ...
```

## Troubleshooting

### Mobile Number Format
- ✅ Correct: `+919876543210`, `919876543210`
- ❌ Wrong: `9876543210` (missing country code)

### OTP Not Working
1. Check console for printed OTP
2. Verify mobile number matches registered number
3. Check OTP hasn't expired (5 minutes)
4. Try requesting new OTP

### "User not registered"
- Register first before attempting login
- Ensure user_type matches (buyer/seller/logistic)

### Token Expired
- Logout and login again
- Tokens expire after 24 hours

## Testing

### Manual Testing
```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"mobile_number": "+919876543210", "user_type": "buyer", "name": "Test User"}'

# Request OTP
curl -X POST http://localhost:8000/api/auth/login/request-otp \
  -H "Content-Type: application/json" \
  -d '{"mobile_number": "+919876543210", "user_type": "buyer"}'

# Verify OTP
curl -X POST http://localhost:8000/api/auth/login/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"mobile_number": "+919876543210", "user_type": "buyer", "otp": "123456"}'
```

## Files Modified

1. **backend/streamlit_auth.py** - Streamlit auth UI (new)
2. **backend/demo_quality_price.py** - Integrated auth check
3. **backend/app/schemas/auth.py** - Auth schemas (new)
4. **backend/app/services/auth_service.py** - Auth logic (new)
5. **backend/app/api/routes/auth.py** - API endpoints (new)
6. **frontend/src/context/AuthContext.jsx** - React auth state (new)
7. **frontend/src/components/Login.jsx** - Login UI (new)
8. **frontend/src/components/Register.jsx** - Register UI (new)
9. **frontend/src/App.jsx** - Protected routes

## Next Steps

- [ ] Integrate SMS service (Twilio/AWS SNS)
- [ ] Add database (PostgreSQL/MongoDB)
- [ ] Implement refresh tokens
- [ ] Add password recovery
- [ ] Multi-factor authentication
- [ ] Role-based access control
- [ ] Admin dashboard
- [ ] User analytics
