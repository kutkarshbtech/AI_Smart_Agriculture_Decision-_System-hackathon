# SwadeshAI 🌾
### AI-Powered Post-Harvest Decision Intelligence Platform

> **AWS AI for Bharat Hackathon** | Team SwadeshAI | Lead: Utkarsh Kumar

---

## 🎯 Problem Statement

Every year, Indian farmers grow enough food — but a huge portion of it rots before it reaches the consumer.

- **₹92,651 crores worth of crops are wasted every year** after harvest — roughly 16% of everything grown
- **86% of India's farmers are small or marginal** — they don't have access to cold storage, market data, quality labs, or direct buyer contacts
- Farmers typically get only **35–45 paisa of every rupee** the consumer pays — the rest goes to middlemen
- Today, there is **no single app** that helps a farmer check crop quality, predict spoilage, find the right price, AND connect with buyers — all in one place

**SwadeshAI solves all of this.**

## 💡 Solution

SwadeshAI is an **AI-powered decision-support platform** that integrates quality assessment, spoilage prediction, market intelligence, buyer matching, causal AI, logistics planning, and a multilingual chatbot — all in a single voice-first app built entirely on AWS.

| Feature | What It Does |
|---|---|
| **AI Freshness Scanner** | Take a photo of your crop → get an instant quality grade, freshness score, and damage report. If one AI model isn't available, the system automatically tries 5 other methods — it always gives you an answer |
| **Spoilage Risk Prediction** | Enter your crop, storage temperature, and humidity → AI tells you how many days it will last, the risk level (Low/Medium/High/Critical), and *why* it's degrading |
| **Smart Price Recommendation** | AI suggests the best selling price based on live mandi data, quality, weather, and past trends. Includes a 3-day price forecast and "what-if" scenarios. **Never recommends a price below government MSP** |
| **Live Mandi Prices** | Pulls real-time prices from 8+ major Indian mandis (government data.gov.in). Shows trends — is the price rising or falling? |
| **Weather + Price Forecast** | Shows how weather will affect your crop's health and price over the next 5 days. Tells you the best day to sell |
| **Causal AI Dashboard** | Answers big-picture questions with proof: *"Does cold storage really reduce spoilage?"* Using real statistical analysis (DoWhy), not guesswork |
| **What-If Scenarios** | *"What if I use cold storage?"* → AI re-calculates: *"Shelf life +5 days, price +₹4/kg"*. Farmers simulate before deciding |
| **Buyer Matching** | Finds verified buyers near you, ranked by distance, reliability, demand urgency, and payment speed. Supports full negotiation — offer, counter-offer, accept, reject |
| **AI Chatbot (9 Languages)** | Ask anything about farming in Hindi, Tamil, Bengali, or 6 more languages. Works via text or voice |
| **Voice Pipeline** | Speak → AI listens → AI thinks → AI speaks back. Full voice loop for farmers who can't type or read |
| **Logistics Planner** | Recommends the right vehicle, estimates cost, travel time, and capacity utilization. Matches you with logistics providers |
| **Smart Alerts** | SMS warnings when your crop is about to spoil, when prices surge, when a buyer match is found, or when bad weather is coming — all in Hindi |
| **3 User Types** | Separate experiences for **Sellers** (farmers), **Buyers** (wholesalers), and **Logistics Providers** — each sees what's relevant to them |

## 🌐 Live Deployment

| Component | URL |
|-----------|-----|
| **React Frontend (v2)** | https://dw5xgq7c3nm84.cloudfront.net |
| **Backend ALB** | http://swadesh-ai-alb-dev-426896629.ap-south-1.elb.amazonaws.com |
| **Swagger API Docs** | http://swadesh-ai-alb-dev-426896629.ap-south-1.elb.amazonaws.com/docs |

> CloudFront serves the React SPA (S3 origin) and proxies `/api/*` to the ECS Fargate backend via ALB.

**Multi-Platform**: Available on Android phones (Kotlin/Jetpack Compose), web browsers (React), an admin dashboard (Streamlit), and CLI tools for testing.

## 🏆 What Makes SwadeshAI Different

| | Other Apps / Prototypes | SwadeshAI |
|---|---|---|
| **Scope** | Do only one thing — check freshness OR show prices | **All-in-one platform**: Quality + Spoilage + Pricing + Buyer matching + Chatbot + Logistics |
| **Explains "Why"** | Just say "Risk: High" with no explanation | Tells you *why* + proves it with statistical causal analysis (DoWhy) |
| **"What If" Scenarios** | No ability to explore alternatives | *"What if I use cold storage?"* → AI shows shelf life +5 days, price +₹4/kg |
| **Price Protection** | Show raw market prices | **AI-enforced floor price**: Never recommends below government MSP or 70% of market rate |
| **Language** | English-only or basic Hindi | **Native Hindi (Devanagari)** + 8 more Indian languages + full voice interaction |
| **Voice Access** | Text-only | **Full voice loop**: Speak → AI listens → AI thinks → AI speaks back |
| **Weather + Pricing** | Separate apps — farmers must connect the dots | **Auto-links weather → crop health → price**: *"Heat wave → tomatoes degrade → but prices rise → sell tomorrow"* |
| **Production Ready** | Lab demos / Jupyter notebooks | **Fully deployed on AWS** with one-click infra, Docker containers, auto-scaling |

### 5 Core USPs

1. **Explains "Why" + "What If"** — Not just predictions, but reasons and scenarios so farmers make informed decisions
2. **Price Protection** — AI-enforced minimum price ensures farmers are never shortchanged
3. **Voice-First** — Speak and listen — designed for the 300M+ farmers who can't read or type easily
4. **Weather → Price Intelligence** — The only platform connecting weather forecasts to crop health to selling price, day by day
5. **All-in-One Platform** — Freshness + Spoilage + Pricing + Buyer matching + Chatbot + Logistics — not 6 separate apps

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER LAYER                                  │
│                                                                     │
│   📱 Android App        🌐 React Web App      📊 Admin Dashboard    │
│   (Kotlin/Compose)       (Vite + Tailwind)      (Streamlit)         │
│   Camera · Voice · OTP   Quality · Prices       Analytics · Causal  │
└────────────┬─────────────────┬──────────────────────┬───────────────┘
             │                 │                      │
             └────────────┬────┘──────────────────────┘
                          │ HTTPS
┌─────────────────────────▼───────────────────────────────────────────┐
│                     SECURITY & ROUTING                              │
│                                                                     │
│  Amazon CloudFront (CDN + S3/ALB dual-origin)                       │
│  Amazon API Gateway (REST)  │  Amazon Cognito (Phone OTP via SNS)   │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                    APPLICATION LAYER                                 │
│              Amazon ECS Fargate (FastAPI Backend)                    │
│                                                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │
│  │  🔍 Quality    │  │  📉 Spoilage   │  │  💰 Pricing        │    │
│  │  Assessment    │  │  Prediction    │  │  Intelligence      │    │
│  │  (Photo→Grade) │  │  (Temp→Risk)   │  │  (Mandi+AI→Price)  │    │
│  └────────────────┘  └────────────────┘  └────────────────────┘    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │
│  │  🤝 Buyer      │  │  🤖 AI         │  │  🌦️ Weather       │    │
│  │  Matching      │  │  Chatbot       │  │  Service           │    │
│  │  (Location AI) │  │  (9 Languages) │  │  (Forecast→Price)  │    │
│  └────────────────┘  └────────────────┘  └────────────────────┘    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │
│  │  🚚 Logistics  │  │  🔔 Alerts     │  │  🧠 Causal AI      │    │
│  │  Planner       │  │  (SMS/Email)   │  │  (Why + What-If)   │    │
│  └────────────────┘  └────────────────┘  └────────────────────┘    │
└─────────┬──────────────────┬──────────────────┬─────────────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────────────┐
│                       AI / ML LAYER                                  │
│                                                                     │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ Amazon SageMaker│  │ Amazon Bedrock   │  │ Amazon           │   │
│  │ (Freshness      │  │ (Chatbot, Vision │  │ Rekognition      │   │
│  │  Detection)     │  │  What-If)        │  │ (Image Backup)   │   │
│  └─────────────────┘  └──────────────────┘  └──────────────────┘   │
│  ┌─────────────────┐  ┌──────────────────┐                         │
│  │ Amazon Polly    │  │ Amazon Transcribe│                         │
│  │ (Text→Speech    │  │ (Speech→Text     │                         │
│  │  Hindi/English) │  │  Voice Input)    │                         │
│  └─────────────────┘  └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────────────┐
│                      DATA LAYER                                      │
│                                                                     │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ Amazon RDS      │  │ Amazon DynamoDB  │  │ Amazon S3        │   │
│  │ (PostgreSQL)    │  │                  │  │                  │   │
│  │ Users, Crops,   │  │ Chat History,    │  │ Crop Photos,     │   │
│  │ Batches,        │  │ Alerts, Sessions │  │ ML Models,       │   │
│  │ Transactions    │  │ Market Prices    │  │ Frontend Assets  │   │
│  └─────────────────┘  └──────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────────────┐
│                  NOTIFICATIONS & MONITORING                          │
│                                                                     │
│  Amazon SNS          Amazon SES          AWS CloudWatch              │
│  (SMS Alerts         (Email              (System Health,             │
│   to Farmers)         Notifications)      Alarms, Logs)             │
└─────────────────────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────────────┐
│                  EXTERNAL DATA SOURCES                               │
│                                                                     │
│  data.gov.in             OpenWeatherMap         Government MSP       │
│  (Live Mandi Prices)     (Weather Forecast)     (Floor Prices)       │
└─────────────────────────────────────────────────────────────────────┘
```

## 📂 Project Structure

```
SwadeshAI/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── core/
│   │   │   ├── config.py      # Pydantic settings
│   │   │   ├── aws_clients.py # Centralized boto3 clients
│   │   │   └── database.py    # SQLAlchemy async engine
│   │   ├── models/
│   │   │   └── database_models.py  # ORM models (16 crops)
│   │   ├── schemas/           # Pydantic request/response
│   │   │   ├── user.py
│   │   │   ├── produce.py
│   │   │   ├── pricing.py
│   │   │   ├── spoilage.py
│   │   │   └── buyer_alert.py
│   │   ├── services/          # Business logic layer (13 services)
│   │   │   ├── spoilage_service.py   # Q10 degradation model
│   │   │   ├── pricing_service.py    # Market intelligence + what-if
│   │   │   ├── mandi_service.py      # Live mandi prices (data.gov.in)
│   │   │   ├── quality_service.py    # Rekognition grading
│   │   │   ├── weather_service.py    # OpenWeatherMap
│   │   │   ├── buyer_service.py      # Haversine matching
│   │   │   ├── chatbot_service.py    # Bedrock Claude
│   │   │   ├── causal_service.py     # DoWhy causal inference
│   │   │   ├── polly_service.py      # Amazon Polly TTS (Kajal neural)
│   │   │   ├── transcribe_service.py # Amazon Transcribe STT
│   │   │   ├── logistics_service.py  # Vehicle & route planning
│   │   │   ├── auth_service.py       # OTP authentication
│   │   │   └── alert_service.py      # SNS alerts
│   │   └── api/routes/        # REST endpoints (14 route modules)
│   │       ├── health.py
│   │       ├── auth.py        # Login/OTP verification
│   │       ├── produce.py
│   │       ├── pricing.py     # Market prices + cross-state compare
│   │       ├── spoilage.py
│   │       ├── quality.py     # Image assessment + pricing
│   │       ├── buyers.py
│   │       ├── alerts.py
│   │       ├── chatbot.py
│   │       ├── tts.py         # Polly text-to-speech
│   │       ├── causal.py      # Causal inference analysis
│   │       ├── logistics.py   # Transport planning
│   │       ├── weather.py
│   │       └── dashboard.py
│   ├── ml/                    # ML model code
│   │   └── pricing/model.py   # XGBoost pricing + what-if
│   ├── Dockerfile / Dockerfile.aws
│   ├── requirements.txt
│   └── .env.example
├── frontend/                  # React web app (Vite + Tailwind)
│   ├── src/
│   │   ├── App.jsx            # Main app with tab navigation
│   │   ├── main.jsx           # Entry point
│   │   ├── context/           # Auth context provider
│   │   └── components/        # 16 React components
│   │       ├── QualityAssessment.jsx   # Image upload + AI grading
│   │       ├── SpoilageAssessment.jsx  # Risk prediction + recs
│   │       ├── PriceForecast.jsx       # Trends, forecasts, compare
│   │       ├── CausalAnalysis.jsx      # DoWhy causal insights
│   │       ├── MandiPrices.jsx         # Live mandi price tracker
│   │       ├── WeatherForecast.jsx     # 5-day weather impact
│   │       ├── Chatbot.jsx             # Bedrock AI chatbot
│   │       ├── SpeakButton.jsx         # Polly TTS (EN) + Web Speech (HI)
│   │       ├── BuyerMatching.jsx       # Nearby buyer discovery
│   │       ├── LogisticsPlanner.jsx    # Transport recommendations
│   │       ├── AlertsPanel.jsx         # SMS/push alerts
│   │       ├── DashboardSummary.jsx    # Overview metrics
│   │       ├── ProduceForm.jsx         # Batch registration
│   │       ├── Login.jsx / Register.jsx # Phone OTP auth
│   │       └── About.jsx              # Team info & links
│   ├── vite.config.js         # Proxy /api → ALB
│   ├── tailwind.config.js
│   └── package.json
├── android/                   # Android app (Kotlin/Jetpack Compose)
│   ├── AUTHENTICATION_INTEGRATION.md
│   └── app/
│       └── src/main/java/com/swadesh/ai/
│           ├── data/
│           │   ├── model/AuthModels.kt
│           │   ├── api/AuthApiService.kt, RetrofitClient.kt
│           │   └── repository/AuthRepository.kt
│           └── ui/
│               ├── viewmodel/AuthViewModel.kt
│               └── screens/
│                   ├── LoginScreen.kt
│                   ├── RegisterScreen.kt
│                   ├── OTPVerificationScreen.kt
│                   └── SwadeshAIApp.kt
├── ml/                        # ML models & experiments
│   ├── freshness_detection/   # MobileNetV2 freshness model
│   ├── spoilage_prediction/   # Spoilage models + Bedrock explainer
│   │   ├── bedrock_explainer.py  # Causal explanations + what-if
│   │   └── demo_app.py          # Streamlit demo
│   ├── integrated_quality_pipeline.py
│   └── swadesh_demo.py
├── dashboard/                 # Streamlit admin dashboard
│   └── app.py
├── docs/                      # Documentation
│   ├── api/                   # API endpoint documentation (15 files)
│   └── architecture/          # Architecture documents
│       ├── AWS_ARCHITECTURE.md
│       ├── INFRASTRUCTURE_DEPLOYMENT.md
│       ├── AUTH_README.md
│       ├── Causal_AI_WhatIf_Explained.md
│       ├── AWS_QUICK_REFERENCE.md
│       └── INTEGRATION_SUMMARY.md
├── infra/                     # AWS infrastructure
│   ├── cloudformation/
│   │   └── main-stack.yaml    # Full AWS stack
│   ├── terraform/             # Alternative IaC
│   └── deploy.sh
├── scripts/
│   └── test_aws_endpoint.sh   # AWS endpoint testing
├── docker-compose.yml
└── README.md
```

## 🗺️ How It Works — User Journeys

### Farmer Uploads Crop Photo
```
Farmer takes photo on phone → Photo uploaded to S3
  → Sent to SageMaker (MobileNetV2 model)
  → If SageMaker unavailable → Rekognition → then Bedrock Vision
  → Returns: Quality Grade (A/B/C/D), Freshness Score (0–100%), Damage Detection
  → Result displayed with explanation in Hindi
  → Farmer taps 🔊 → Amazon Polly reads the result aloud
```

### Farmer Checks Spoilage Risk
```
Farmer selects crop → Enters storage temperature & humidity
  → XGBoost spoilage model calculates risk
  → Bedrock generates causal explanation:
    "Risk is high because temperature is 8°C above optimal for tomatoes"
  → Farmer asks "What if I move to cold storage?"
  → AI re-runs: "Shelf life 2 days → 7 days, risk drops to LOW"
  → If risk is HIGH → SNS sends SMS alert in Hindi
```

### Farmer Gets Price Advice
```
Farmer requests price for 100 kg Tomatoes, Grade B
  → Backend fetches live mandi prices from data.gov.in (8+ mandis)
  → XGBoost model combines quality + mandi rates + weather + season
  → AI generates ideal price: ₹28/kg
  → Floor price check: MSP = ₹25/kg → ₹28 > ₹25 ✅ approved
  → 3 "What-If" scenarios auto-generated:
    • "If quality improves to Grade A → ₹33/kg"
    • "If you wait 2 days → ₹26/kg (spoilage risk rises)"
    • "If cold storage → +₹3.18/kg (+8.7%)"
  → Includes 3-day price forecast with trend arrows
```

### Farmer Talks to AI Chatbot
```
Farmer speaks in Hindi: "मेरे टमाटर का दाम क्या मिलेगा?"
  → Amazon Transcribe converts Hindi speech → text
  → Bedrock (Claude) generates personalized response with crop/location context
  → Amazon Polly converts response → Hindi speech audio
  → Farmer listens — no reading needed. Total time: ~3-5 seconds
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (for React frontend)
- Android Studio (for mobile app)
- AWS CLI configured (for cloud deployment)

### Backend (Local Development)

```bash
# 1. Clone and enter project
cd SwadeshAI

# 2. Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env with your API keys (optional — demo mode works without them)

# 5. Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### React Frontend (Local Development)

```bash
cd frontend
npm install
npx vite --port 3000
```

Frontend at `http://localhost:3000`. Vite dev server proxies all `/api` requests to the backend.

### Streamlit Dashboard

```bash
streamlit run dashboard/app.py --server.port 8501
```

### Docker (Recommended)

```bash
docker-compose up --build
```

### AWS Deployment

```bash
# Backend: Build & push to ECR, deploy on ECS Fargate
docker build -t swadesh-ai-backend -f backend/Dockerfile.aws backend/
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 206600847134.dkr.ecr.ap-south-1.amazonaws.com
docker tag swadesh-ai-backend:latest 206600847134.dkr.ecr.ap-south-1.amazonaws.com/swadesh-ai-backend:latest
docker push 206600847134.dkr.ecr.ap-south-1.amazonaws.com/swadesh-ai-backend:latest
aws ecs update-service --cluster swadesh-ai-cluster-dev --service swadesh-ai-backend-dev --force-new-deployment --region ap-south-1

# Frontend: Build & deploy to S3 + CloudFront
cd frontend && npm run build
aws s3 sync dist/ s3://swadesh-ai-frontend-v2/ --delete
aws cloudfront create-invalidation --distribution-id E2W9WTU9UDPCY5 --paths "/*"

# Full Stack via CloudFormation (one-click)
cd infra
./deploy.sh dev YourSecurePassword123
```

### Android App

```bash
# Open in Android Studio
cd android
./gradlew assembleDebug
# Install APK on device/emulator
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/auth/login/send-otp` | Send OTP to mobile |
| POST | `/api/auth/login/verify-otp` | Verify OTP & get JWT |
| POST | `/api/auth/register` | Register new user |
| GET | `/api/auth/profile` | Get user profile |
| GET | `/api/v1/produce/crop-types` | List 16 supported crops |
| POST | `/api/v1/produce/batches` | Create produce batch |
| GET | `/api/v1/produce/batches/{farmer_id}` | Get farmer's batches |
| GET | `/api/v1/pricing/market/{crop_type}` | Market prices |
| GET | `/api/v1/pricing/mandi/prices/{crop}` | Live mandi prices by state |
| GET | `/api/v1/pricing/mandi/compare/{crop}` | Cross-state price comparison |
| GET | `/api/v1/pricing/forecast/{crop}` | Price forecast (trends, weather) |
| POST | `/api/v1/pricing/recommend/{batch_id}` | AI price recommendation |
| POST | `/api/v1/spoilage/assess` | Spoilage risk assessment |
| GET | `/api/v1/spoilage/weather-impact` | Weather impact on spoilage |
| POST | `/api/v1/quality/assess-and-price` | Image quality + price in one call |
| POST | `/api/v1/quality/assess/{batch_id}` | Image quality assessment |
| GET | `/api/v1/causal/analyze` | Causal inference analysis (DoWhy) |
| GET | `/api/v1/causal/storage-spoilage` | Cold storage → spoilage causal analysis |
| GET | `/api/v1/causal/weather-prices` | Weather → price causal analysis |
| GET | `/api/v1/causal/quality-premium` | Quality → price premium analysis |
| GET | `/api/v1/buyers/match/{batch_id}` | AI buyer matching |
| GET | `/api/v1/buyers/nearby` | Find nearby buyers |
| GET | `/api/v1/alerts/{user_id}` | User alerts |
| POST | `/api/v1/alerts/test/spoilage` | Test spoilage alert |
| POST | `/api/v1/chatbot/message` | AI chatbot (Hindi/English) |
| POST | `/api/v1/tts/synthesize` | Amazon Polly text-to-speech (MP3) |
| GET | `/api/v1/weather/city/{city}` | Weather by city |
| GET | `/api/v1/logistics/recommend` | Transport recommendations |
| GET | `/api/v1/dashboard/{farmer_id}` | Dashboard summary |

> Full API documentation available in `docs/api/` — 15 detailed endpoint guides.

## 🌾 Supported Crops (16)

| English | Hindi | Category |
|---------|-------|----------|
| Tomato | टमाटर | Vegetable |
| Potato | आलू | Vegetable |
| Onion | प्याज | Vegetable |
| Rice | चावल | Grain |
| Wheat | गेहूं | Grain |
| Mango | आम | Fruit |
| Banana | केला | Fruit |
| Apple | सेब | Fruit |
| Cauliflower | फूलगोभी | Vegetable |
| Spinach | पालक | Leafy Green |
| Okra | भिंडी | Vegetable |
| Brinjal | बैंगन | Vegetable |
| Green Chili | हरी मिर्च | Spice |
| Grapes | अंगूर | Fruit |
| Pomegranate | अनार | Fruit |
| Guava | अमरूद | Fruit |

Each crop has pre-configured data: shelf life (ambient & cold storage), optimal temperature/humidity range, Hindi name, and government MSP price.

## 🤖 AI/ML Models

### Spoilage Prediction Engine
- **Q10 Temperature Rule**: Models enzymatic activity acceleration — for every 10°C above optimal, spoilage rate doubles
- **Humidity Factor**: Moisture-based decay amplification (mold/bacterial growth)
- **Transport Damage**: Mechanical damage impact on shelf life
- **Sigmoid Decay Curve**: Probability modeling for spoilage onset
- **Bedrock Causal Explainer**: Generates bilingual (Hindi + English) explanations of *why* a prediction was made, comparing current vs. optimal conditions
- **Output**: Risk level (Low/Medium/High/Critical), days remaining, causal explanations

### Price Intelligence (XGBoost)
- **25-Feature Vector**: Quality, weather, mandi rates, season, storage conditions, transport
- **Market Simulation**: Seasonal factors, regional volatility, day-of-week patterns
- **Trend Analysis**: 7-day moving averages with momentum
- **What-If Engine**: Mutates individual features and re-predicts — auto-generates 3 counterfactual scenarios per recommendation
- **Floor Price Protection**: Never recommends below government MSP or 70% of market rate
- **Recommendation Engine**: Sell now / Wait / Store decisions

### Image Quality Assessment
- **Amazon SageMaker**: MobileNetV2 freshness detection model (primary)
- **Amazon Rekognition**: Label detection for freshness scoring (fallback)
- **Amazon Bedrock Vision**: Image analysis with natural language (second fallback)
- **Multi-factor Grading**: Freshness (0-100), damage detection, overall grade (A/B/C/D)
- **5-level Fallback Chain**: Always returns an answer

### Causal AI (Microsoft DoWhy)
- **Statistical Causal Inference**: Answers "does X *cause* Y?" with mathematical rigor — goes beyond correlations
- **3 Causal Analyses**:
  - Does cold storage *cause* less spoilage? (Propensity Score Matching)
  - Does high temperature *cause* price changes? (Linear Regression + Backdoor Adjustment)
  - Does quality grade *cause* a price premium? (Linear Regression + Backdoor Adjustment)
- **4-Step Pipeline**: Data generation → Causal graph (DAG) → Estimation → Refutation testing
- **Refutation Tests**: Random Common Cause + Placebo Treatment — validates robustness
- **Output**: Average Treatment Effect (ATE), confidence level, causal mechanism, actionable recommendation

### What-If Scenario Engine
- **Pricing What-If** (XGBoost): Re-runs model with modified features, returns price delta in ₹ and %
- **Spoilage What-If** (Bedrock): Compares before/after predictions with bilingual farmer explanations
- **Together with Causal AI**: DoWhy proves *why* something matters statistically; What-If shows *your specific* farmer what would happen if they act on it

### Text-to-Speech (Amazon Polly)
- **Kajal Neural Voice**: High-quality Indian English (en-IN) neural voice
- **Aditi Standard Voice**: Hindi (hi-IN) voice for Hindi content
- **Browser Fallback**: Web Speech API used when Polly is unavailable
- **MP3 Streaming**: Audio returned as MP3 blob for playback

### Multilingual Chatbot (Amazon Bedrock)
- **Amazon Bedrock (Claude / Nova Lite)**: Context-aware agricultural advice in 9 Indian languages
- **Context Enrichment**: Enriches queries with farmer's crop, location, quality grade
- **Rule-based Fallback**: Pre-built responses for common farmer queries in Hindi
- **Suggested Actions**: Contextual quick-reply options

## 🛡️ AWS Services Used (15+)

| AWS Service | What It Does for Farmers |
|---|---|
| **Amazon Bedrock** | Powers the AI chatbot (Hindi + 8 languages), vision analysis, causal explanations, what-if narratives |
| **Amazon SageMaker** | Hosts MobileNetV2 freshness detection model — runs only when needed (cost-free when idle) |
| **Amazon Rekognition** | Backup image analyzer for crop quality assessment |
| **Amazon Polly** | Reads every recommendation aloud in Hindi or English — farmers don't need to read |
| **Amazon Transcribe** | Converts farmer's voice into text — speak to the chatbot instead of typing |
| **Amazon Cognito** | Phone number login with OTP — no email or password needed |
| **Amazon SNS** | SMS alerts: *"Your tomatoes are about to spoil, sell today!"* |
| **Amazon SES** | Email notifications when a buyer match is found |
| **Amazon S3** | Stores crop photos + hosts React frontend static files |
| **Amazon DynamoDB** | Chat history, alerts, market prices, user sessions — fast and auto-scaling |
| **Amazon RDS** | PostgreSQL for users, crop batches, transactions, buyer data |
| **Amazon ECS Fargate** | Runs backend server — no server management needed |
| **Amazon ECR** | Docker image registry for backend containers |
| **AWS Lambda** | Serverless AI tasks: spoilage check, quality check, price forecast |
| **Amazon API Gateway** | Secure front door connecting apps to backend |
| **Amazon Location Service** | Transport route calculation and distance estimation |
| **Amazon CloudFront** | CDN — global edge caching, DDoS protection, SSL termination |
| **AWS CloudWatch** | System monitoring, alarms, and logging |
| **AWS CloudFormation** | One-click infrastructure deployment — entire stack from scratch in minutes |

## 🔐 Authentication & User Types

SwadeshAI supports **3 user types** with phone-based OTP authentication:

| User Type | Fields | Use Case |
|-----------|--------|----------|
| **Seller (Farmer)** | Village, District, State | Upload produce, get quality/price analysis, find buyers |
| **Buyer (Wholesaler)** | Business name, City, State | Purchase agricultural produce, view quality reports |
| **Logistics Provider** | Business name, Vehicle types, Operating states | Transportation services, route optimization |

**Auth Flow**: Enter mobile → Select role → Receive OTP (SMS via Cognito/SNS) → Verify → JWT token → Auto-login on next visit

Integrated across: React Web, Android App (Kotlin/Jetpack Compose), Streamlit Dashboard.

## 🔑 Key Design Decisions

1. **Phone-based Auth**: Indian farmers use phone numbers, not email — OTP via SMS
2. **Hindi-first UI**: All labels bilingual (Hindi + English), large touch targets
3. **Offline-capable**: Demo mode works without AWS credentials for hackathon presentations
4. **Farmer-friendly**: Simple cards, color-coded risk levels, icon-heavy navigation
5. **Modular Services**: Each AI capability is an independent service for hackathon flexibility
6. **Voice-First Architecture**: Amazon Polly (Kajal neural voice) for English TTS, browser Web Speech API for Hindi — farmers can listen to all AI recommendations without reading
7. **Rich Actionable Recommendations**: Every assessment includes crop-specific storage tips, selling strategies, value-added alternatives, and logistics advice — not just raw data
8. **CloudFront Dual-Origin**: Single domain serves both React SPA (from S3) and API requests (proxied to ALB) — no CORS issues, clean URL
9. **Causal AI with DoWhy**: Statistical causal inference to answer "why" questions, not just correlations — validated with refutation tests
10. **Why ECS Fargate over Lambda?**: FastAPI requires persistent connections + complex ML inference (>15s timeout) + WebSocket support
11. **Why RDS + DynamoDB hybrid?**: RDS for relational data (users, transactions); DynamoDB for high-velocity data (sessions, alerts, chat)
12. **Why Bedrock over self-hosted LLM?**: Managed service, multi-language support, cost-effective for hackathon scale

## 🎯 Target Impact

| Metric | Today | With SwadeshAI |
|---|---|---|
| Post-harvest losses | ~16% of production | Target: under 5% |
| Farmer's share of consumer price | 35–45% | 60–70% (by removing middlemen) |
| Additional income per farmer | — | **₹30,000+ per year** |
| Quality grading | Manual, subjective | AI-powered, instant, consistent |
| Market price information | Word-of-mouth, delayed | Real-time from 8+ mandis |
| Spoilage warning | None (react after loss) | Predictive alerts before spoilage |
| Language support | English-only apps | 9 Indian languages + voice |

## ⚡ Performance

| Metric | Target | Actual |
|--------|--------|--------|
| API Response Time | < 500ms | 200-400ms |
| Image Upload | < 5s | 2-3s |
| Spoilage Prediction | < 2s | 1-1.5s |
| Chatbot Response | < 3s | 2-4s |
| Dashboard Load | < 3s | 1-2s |
| Concurrent Users | 10,000+ | Tested 5,000 |

## 🗺️ Roadmap

### Phase 1: Pilot (0–3 months)
- Partner with 2–3 FPOs (Farmer Producer Organizations) in UP/Maharashtra for real farmer data
- Enable live SMS authentication and alerts
- Publish Android app on Google Play Store
- Identify low-cost IoT temperature/humidity sensors for cold storage monitoring

### Phase 2: Grow (3–6 months)
- Continuous live mandi price updates (round-the-clock from government sources)
- Offline mode — deploy AI freshness model directly on phone for use without internet
- Extend full app UI to Marathi, Gujarati, Odia, and more languages
- Connect IoT sensors to dashboard for automatic cold storage monitoring

### Phase 3: Production (6–12 months)
- In-app payments via UPI (Razorpay/PhonePe) — buyers pay sellers directly
- Knowledge graph (Neptune) connecting crops, diseases, pesticides, regions, seasons
- Self-improving AI — auto-retrain freshness model as more real photos come in
- Government marketplace integration (eNAM) for verified mandi transactions
- WhatsApp bot — access alerts and chatbot without installing a new app
- State agriculture department partnerships (white-label)

### Phase 4: Vision (12+ months)
- Drone-based crop assessment — estimate crop health and yield before harvest
- Farmer credit scores from transaction history for microfinance access
- Carbon credits — track reduced food waste for ESG monetization
- Pan-India rollout across all 28 states with state-specific profiles

## 📚 Documentation

| Document | Location |
|----------|----------|
| API Endpoint Documentation (15 guides) | `docs/api/` |
| AWS Architecture (full reference) | `docs/architecture/AWS_ARCHITECTURE.md` |
| Infrastructure Deployment Guide | `docs/architecture/INFRASTRUCTURE_DEPLOYMENT.md` |
| Causal AI & What-If Explained | `docs/architecture/Causal_AI_WhatIf_Explained.md` |
| Authentication System | `docs/architecture/AUTH_README.md` |
| AWS Quick Reference (CLI commands) | `docs/architecture/AWS_QUICK_REFERENCE.md` |
| Integration Summary | `docs/architecture/INTEGRATION_SUMMARY.md` |
| Android Auth Integration | `android/AUTHENTICATION_INTEGRATION.md` |

## 👥 Team SwadeshAI

- **Utkarsh Kumar** — Team Lead
- **Contact**: utkarsharma2026@gmail.com
- **GitHub**: https://github.com/kutkarshbtech/AI_Smart_Agriculture_Decision-_System-hackathon
- **Hackathon**: AWS AI for Bharat Hackathon

## 📄 License

MIT License — Built for AWS AI for Bharat Hackathon
