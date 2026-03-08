# Spoilage Prediction — XGBoost ML Model

## Overview
XGBoost-based multi-output model that predicts produce spoilage risk for 16 Indian crops.
Uses synthetic training data generated from agricultural science (Q10 temperature rule, humidity impact, transport damage, respiration rates).

**AWS Services Used:**
- **Amazon Bedrock (Claude)** — Causal Explanation Engine: generates rich, farmer-friendly explanations in Hindi + English
- **Amazon SageMaker** — Model deployment: serverless or real-time endpoints

## What It Predicts
| Output | Type | Description |
|--------|------|-------------|
| Remaining shelf life | Regression (days) | How many days before produce spoils |
| Spoilage probability | Regression (0-1) | Likelihood of spoilage at current conditions |
| Risk level | Classification | Low / Medium / High / Critical |

## Supported Crops (16)
| Crop | Hindi | Category |
|------|-------|----------|
| Tomato | टमाटर | Vegetable |
| Potato | आलू | Vegetable |
| Onion | प्याज | Vegetable |
| Banana | केला | Fruit |
| Mango | आम | Fruit |
| Apple | सेब | Fruit |
| Rice | चावल | Grain |
| Wheat | गेहूं | Grain |
| Cauliflower | फूलगोभी | Vegetable |
| Spinach | पालक | Leafy Green |
| Okra | भिंडी | Vegetable |
| Brinjal | बैंगन | Vegetable |
| Grape | अंगूर | Fruit |
| Guava | अमरूद | Fruit |
| Carrot | गाजर | Vegetable |
| Capsicum | शिमला मिर्च | Vegetable |

## Features Used
| Feature | Description |
|---------|-------------|
| `crop_type_idx` | Encoded crop type (0-15) |
| `storage_type` | 0=ambient, 1=cold storage |
| `temperature_c` | Current storage temperature (°C) |
| `humidity_pct` | Current relative humidity (%) |
| `days_since_harvest` | Days since harvest |
| `transport_hours` | Hours in transit |
| `initial_quality_score` | Quality at harvest (0-100) |
| `quantity_kg` | Batch size in kg |
| `damage_sensitivity` | Crop-specific damage sensitivity (0-1) |
| `base_shelf_life_days` | Base shelf life for crop+storage combo |
| `temp_deviation` | Degrees from optimal temperature range |
| `humidity_deviation` | Points from optimal humidity range |
| `respiration_multiplier` | Crop respiration rate factor |

## Quick Start

```bash
cd ml/spoilage_prediction

# Install dependencies
pip install -r requirements.txt

# Generate data + train + evaluate (one command)
python train.py

# Quick training (smaller dataset)
python train.py --preset fast --samples 10000

# Best quality training
python train.py --preset accurate --samples 100000
```

## Step-by-Step

### 1. Generate Dataset
```bash
python dataset.py --samples 50000
```
Creates synthetic data in `data/` with train/val/test splits.

### 2. Train Model
```bash
python train.py --preset balanced
```
Presets: `fast` (200 trees), `balanced` (500 trees), `accurate` (1000 trees)

### 3. Evaluate
```bash
python evaluate.py --detailed
```

### 4. Run Inference
```bash
# Single prediction
python inference.py --crop tomato --temp 35 --humidity 60 --days 3

# With transport and cold storage
python inference.py --crop banana --temp 13 --humidity 85 --days 2 --storage cold --transport 6

# With Amazon Bedrock-powered causal explanations
python inference.py --crop tomato --temp 35 --humidity 60 --days 3 --bedrock

# What-if scenario analysis
python inference.py --crop tomato --temp 35 --humidity 60 --days 3 \
    --whatif '{"storage_type": "cold", "temperature": 12, "humidity": 90}'

# Batch prediction from CSV
python inference.py --csv data/spoilage_test.csv --output results.json

# Demo (multiple crops)
python inference.py
```

### 5. Export for Deployment
```bash
python export_model.py --format joblib       # FastAPI backend
python export_model.py --format sagemaker    # AWS SageMaker
python export_model.py --format all          # All formats
```

### 6. Deploy to SageMaker
```bash
# Serverless endpoint (pay-per-request, $0 when idle — ideal for hackathon)
python sagemaker_deploy.py --mode serverless

# Real-time endpoint (always warm, ~$0.05/hr)
python sagemaker_deploy.py --mode realtime

# Test the live endpoint
python sagemaker_deploy.py --test --crop tomato --temp 35

# Delete the endpoint
python sagemaker_deploy.py --delete
```

## Architecture

```
                        ┌────────────────────────────┐
                        │     User Input (CLI/API)   │
                        └────────────┬───────────────┘
                                     │
                        ┌────────────▼───────────────┐
                        │   SpoilagePredictor        │
                        │   (inference.py)            │
                        └────────────┬───────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
    ┌─────────▼──────────┐  ┌───────▼────────┐  ┌─────────▼──────────┐
    │  XGBoost Model     │  │  Bedrock        │  │  Recommendations   │
    │  (3 sub-models)    │  │  Explainer      │  │  Engine             │
    │                    │  │  (Claude)       │  │  (template-based)   │
    │  ┌──────┐ ┌─────┐ │  │                 │  │                    │
    │  │Shelf │ │Risk │ │  │  Causal         │  │  Hindi + English   │
    │  │Life  │ │Level│ │  │  explanations   │  │  advice            │
    │  └──────┘ └─────┘ │  │  in Hindi +     │  │                    │
    │  ┌──────┐         │  │  English        │  │  What-if scenarios │
    │  │Prob  │         │  │                 │  │                    │
    │  └──────┘         │  │  Fallback:      │  └────────────────────┘
    │                   │  │  template-based │
    └───────────────────┘  └────────────────┘

    Amazon SageMaker          Amazon Bedrock
    (deployment)              (Claude 3 Sonnet)
```

## Science Behind the Model

- **Q10 Temperature Rule**: Enzymatic activity roughly doubles for every 10°C increase above optimal
- **Humidity Impact**: Below-optimal causes moisture loss/wilting; above-optimal promotes mold
- **Transport Damage**: Mechanical stress from transit, weighted by crop sensitivity
- **Respiration Rate**: Climacteric fruits (banana, mango) spoil faster due to ethylene production
- **Sigmoid Decay**: Spoilage probability follows a sigmoid curve centered at 60% of shelf life

## Output Example

```json
{
  "crop": "tomato",
  "crop_hindi": "टमाटर",
  "risk_level": "high",
  "risk_icon": "🔴",
  "spoilage_probability": 0.72,
  "remaining_shelf_life_days": 1.5,
  "recommendations": [
    {
      "en": "Sell within 1-2 days to prevent losses.",
      "hi": "नुकसान से बचने के लिए 1-2 दिन में बेच दें।"
    }
  ],
  "explanation": {
    "en": "Storage temperature (35°C) is 20°C above optimal, accelerating spoilage.",
    "hi": "भंडारण तापमान (35°C) इष्टतम से 20°C अधिक है, जिससे खराबी तेज़ हो रही है।"
  }
}
```

## AWS Integration

### Amazon Bedrock — Causal Explanation Engine

The `bedrock_explainer.py` module uses Claude 3 Sonnet via Amazon Bedrock to generate
rich, contextual causal explanations that go beyond templates:

| Feature | Template-based | Bedrock-powered |
|---------|---------------|-----------------|
| Q10 rule explanation | ✅ Basic | ✅ Contextual with comparisons |
| Key causes identified | ✅ 2-3 factors | ✅ 3-5 with cause→effect chains |
| Controllable vs uncontrollable | ❌ | ✅ |
| What-if scenarios | ✅ Basic | ✅ Rich comparative analysis |
| Language quality | Good | Natural, farmer-friendly |
| Fallback when offline | — | ✅ Auto-falls back to templates |

**Configuration:**
```bash
export BEDROCK_REGION=ap-south-1
export BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

### Amazon SageMaker — Model Deployment

The `sagemaker_deploy.py` script deploys the XGBoost model as a SageMaker endpoint:

- **Serverless** (default): Pay-per-request, auto-scales to zero — $0 when idle
- **Real-time**: Always-on with sub-100ms latency
- IAM role includes Bedrock invoke permissions for explanation engine

## File Structure

```
spoilage_prediction/
├── dataset.py           # Synthetic data generation (16 Indian crops)
├── model.py             # XGBoost multi-output model (3 sub-models)
├── train.py             # Training pipeline with presets
├── inference.py         # Production inference + Bedrock integration
├── evaluate.py          # Model evaluation with per-crop breakdown
├── export_model.py      # Export to joblib/ONNX/SageMaker
├── bedrock_explainer.py # Amazon Bedrock Causal Explanation Engine
├── sagemaker_deploy.py  # Amazon SageMaker deployment script
├── requirements.txt
├── README.md
├── models/              # Trained model artifacts
│   ├── spoilage_v1_shelf_life.joblib
│   ├── spoilage_v1_probability.joblib
│   ├── spoilage_v1_risk.joblib
│   ├── spoilage_v1_metadata.json
│   └── sagemaker_model.tar.gz
└── data/                # Generated datasets
```
