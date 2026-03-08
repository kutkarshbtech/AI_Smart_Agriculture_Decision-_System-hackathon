# SwadeshAI Android Authentication Integration

## ✅ Complete Integration Status

Your SwadeshAI Android app now has **full authentication integration** with the backend API, supporting three user types:

### 🎭 Three User Types
1. **Buyer** - Purchases agricultural produce
2. **Seller** - Farmers/vendors selling produce
3. **Logistic Provider** - Transportation and logistics services

---

## 📱 What's Been Implemented

### Backend (Python/FastAPI)
- ✅ Added `auth` router to main.py
- ✅ Authentication API endpoints:
  - `POST /api/auth/register` - Register new user
  - `POST /api/auth/login/request-otp` - Request OTP
  - `POST /api/auth/login/verify-otp` - Verify OTP & login
  - `GET /api/auth/profile` - Get user profile
  - `POST /api/auth/logout` - Logout

### Android App (Kotlin/Jetpack Compose)
#### 📦 Data Layer
- ✅ `AuthModels.kt` - Data models for all auth responses/requests
- ✅ `AuthApiService.kt` - Retrofit interface for auth endpoints
- ✅ `AuthRepository.kt` - Local storage using DataStore
- ✅ Updated `RetrofitClient.kt` - Added auth API service

#### 🎨 UI Layer
- ✅ `LoginScreen.kt` - Mobile number & user type selection
- ✅ `RegisterScreen.kt` - Registration with user-specific fields
- ✅ `OTPVerificationScreen.kt` - OTP entry and verification

#### 🏗️ ViewModel
- ✅ `AuthViewModel.kt` - Manages auth state and API calls

#### 🧭 Navigation
- ✅ Updated `SwadeshAIApp.kt` - Complete auth flow integration
  - Login → Register → OTP → Dashboard
  - Persistent login state
  - Logout functionality

---

## 🚀 How to Run

### 1. Start Backend Server
```powershell
cd SwadeshAI\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Initialize Database Tables
```powershell
# Make sure PostgreSQL is running
cd SwadeshAI\backend
python init_auth_tables.py
```

### 3. Build and Run Android App
```powershell
# From Android Studio, or via command line:
cd SwadeshAI\android
./gradlew assembleDebug
# Then install APK on device/emulator
```

---

## 🔑 Authentication Flow

### New User Registration Flow
1. User opens app → Sees Login screen
2. Clicks "New user? Register here"
3. Selects user type (Buyer/Seller/Logistic)
4. Fills in details:
   - **Buyer**: Name, Business name, City, State
   - **Seller**: Name, Village, District, State
   - **Logistic**: Name, Business name, Vehicle types, Operating states
5. Clicks "Register"
6. Redirected back to Login screen

### Login Flow
1. User enters mobile number
2. Selects user type
3. Clicks "Get OTP"
4. Backend sends OTP (in demo mode, OTP is displayed on screen)
5. User enters OTP
6. Clicks "Verify OTP"
7. Successfully logged in → Navigates to Dashboard

### Session Management
- Token stored securely using DataStore (encrypted)
- Auto-login on app restart if token valid
- Logout button in app bar clears session

---

## 📋 User Type Specific Fields

### Buyer
```kotlin
{
  "mobile_number": "+919876543210",
  "user_type": "buyer",
  "name": "Ramesh Traders",
  "business_name": "Ramesh Wholesale",
  "city": "Mumbai",
  "state": "Maharashtra",
  "pincode": "400001"
}
```

### Seller
```kotlin
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

### Logistic Provider
```kotlin
{
  "mobile_number": "+917654321098",
  "user_type": "logistic",
  "name": "Vijay Transport",
  "business_name": "Vijay Logistics",
  "vehicle_types": ["Truck", "Tempo"],
  "operating_states": ["Maharashtra", "Gujarat"],
  "city": "Pune",
  "state": "Maharashtra"
}
```

---

## 🛠️ API Configuration

### Backend URL
- **Debug**: `http://10.0.2.2:8000/api/v1/` (Android emulator loopback)
- **Release**: `https://api.swadesh.ai/api/v1/` (production)

Update in `app/build.gradle.kts`:
```kotlin
buildConfigField("String", "BASE_URL", "\"http://10.0.2.2:8000/api/v1/\"")
```

### Testing with Physical Device
If using a physical Android device, replace `10.0.2.2` with your computer's local IP:
```kotlin
buildConfigField("String", "BASE_URL", "\"http://192.168.x.x:8000/api/v1/\"")
```

---

## 📱 Screen Navigation Map

```
App Launch
    ↓
[Check if logged in]
    ↓
    ├─ Yes → Dashboard
    │         ↓
    │    [Bottom Navigation]
    │    - Dashboard
    │    - My Produce
    │    - Scanner
    │    - Prices
    │    - Chat AI
    │         ↓
    │    [Logout] → Login
    │
    └─ No → Login Screen
              ↓
         [Get OTP] → OTP Verification
              ↓              ↓
         [Register]    [Verify] → Dashboard
```

---

## 🔐 Security Features

1. **Token-based Authentication**
   - Bearer token sent in Authorization header
   - 24-hour expiry (configurable)

2. **OTP Verification**
   - 6-digit OTP
   - Time-limited validity
   - Retry mechanism

3. **Secure Storage**
   - Credentials stored using DataStore (encrypted)
   - No plaintext passwords
   - Auto-logout on token expiry

---

## 🐛 Troubleshooting

### Can't connect to backend
**Issue**: Network error when clicking "Get OTP"

**Solutions**:
1. Ensure backend is running: `curl http://localhost:8000/health`
2. Check Android emulator can reach backend: Use `10.0.2.2` not `localhost`
3. For physical device: Use computer's IP address in BASE_URL
4. Check firewall isn't blocking port 8000

### Database connection refused
**Issue**: Backend can't connect to PostgreSQL

**Solutions**:
1. Start PostgreSQL: `net start postgresql-x64-15` (Windows)
2. Verify connection string in `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/swadesh_ai
   ```
3. Run table initialization: `python init_auth_tables.py`

### OTP not working
**Issue**: "Invalid OTP" error

**Solutions**:
1. Check demo OTP displayed on screen (demo mode)
2. Verify OTP hasn't expired (usually 5-10 minutes)
3. Ensure correct user type selected
4. Check backend logs for OTP generation

### App crashes on login
**Issue**: App force closes when clicking login

**Solutions**:
1. Check Android Logcat for error messages
2. Verify all dependencies installed (Retrofit, DataStore)
3. Sync Gradle project
4. Clean and rebuild: `./gradlew clean build`

---

## 📁 File Structure

```
android/app/src/main/java/com/swadesh/ai/
├── data/
│   ├── model/
│   │   └── AuthModels.kt          # Data models
│   ├── api/
│   │   ├── AuthApiService.kt      # API interface
│   │   └── RetrofitClient.kt      # HTTP client
│   └── repository/
│       └── AuthRepository.kt      # Local storage
├── ui/
│   ├── screens/
│   │   ├── LoginScreen.kt         # Login UI
│   │   ├── RegisterScreen.kt      # Registration UI
│   │   ├── OTPVerificationScreen.kt  # OTP UI
│   │   └── SwadeshAIApp.kt        # Navigation
│   └── viewmodel/
│       └── AuthViewModel.kt       # Business logic
└── MainActivity.kt
```

---

## ✨ Features Summary

✅ Three user types (Buyer, Seller, Logistic)  
✅ Phone-based OTP authentication  
✅ User-specific registration fields  
✅ Persistent login sessions  
✅ Secure token storage  
✅ Clean Material Design 3 UI  
✅ Full navigation flow  
✅ Error handling and validation  
✅ Logout functionality  
✅ Demo mode with visible OTP  

---

## 🎯 Next Steps

1. **Test on Android Emulator**
   - Create AVD in Android Studio
   - Run app and test full auth flow

2. **Test Production Features**
   - Remove demo OTP display (security)
   - Integrate real SMS gateway (Twilio, AWS SNS)
   - Add phone number verification

3. **Enhance UI**
   - Add loading animations
   - Improve error messages
   - Add input validation feedback

4. **Add More Features**
   - Forgot password/OTP resend with cooldown
   - Profile editing
   - User avatar upload
   - Language selection

---

## 📞 API Testing

Test backend endpoints using curl:

```bash
# Register new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"mobile_number":"+919876543210","user_type":"seller","name":"Test User"}'

# Request OTP
curl -X POST http://localhost:8000/api/auth/login/request-otp \
  -H "Content-Type: application/json" \
  -d '{"mobile_number":"+919876543210","user_type":"seller"}'

# Verify OTP (use OTP from response)
curl -X POST http://localhost:8000/api/auth/login/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"mobile_number":"+919876543210","user_type":"seller","otp":"123456"}'

# Get profile (use token from verify response)
curl http://localhost:8000/api/auth/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🎉 Congratulations!

Your SwadeshAI app now has complete authentication integration supporting three distinct user types with a modern, secure authentication flow!
