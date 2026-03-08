# SageMaker Deployment — Freshness Detection Model

Deploy the SwadeshAI freshness detection model (MobileNetV2, 97.7% accuracy) to **AWS SageMaker Serverless Inference**.

## Architecture

```
Android App / FastAPI Backend
        │
        ▼
   API Gateway
        │
        ▼
  SageMaker Endpoint  (Serverless — scales to zero)
        │
        ▼
   ONNX Runtime (MobileNetV2, 0.3 MB)
        │
        ▼
   { quality_score, freshness, damage, recommendations }
```

## Prerequisites

```bash
# 1. AWS CLI configured
aws configure   # Region: ap-south-1

# 2. Python packages
pip install boto3 sagemaker onnx onnxruntime

# 3. ONNX model exported (from the ml/freshness_detection/ directory)
cd ml/freshness_detection
python export_model.py --model models/freshness_v1_best.pth --format onnx
# → models/freshness_v1_best.onnx (0.3 MB)
```

## Quick Deploy

```bash
cd ml/freshness_detection/sagemaker

# Deploy (serverless — $0 when idle, ~$0.0001 per inference)
python deploy_sagemaker.py --mode serverless

# Or: always-on endpoint (~$0.05/hr)
python deploy_sagemaker.py --mode realtime
```

## Test the Endpoint

```bash
# With an image file
python deploy_sagemaker.py --test --image ../samples/test_banana.jpg

# From Python
python -c "
import boto3, json
runtime = boto3.client('sagemaker-runtime', region_name='ap-south-1')
response = runtime.invoke_endpoint(
    EndpointName='swadesh-ai-freshness-detector-endpoint',
    ContentType='image/jpeg',
    Body=open('../samples/test_banana.jpg', 'rb').read()
)
result = json.loads(response['Body'].read())
print(json.dumps(result, indent=2, ensure_ascii=False))
"
```

## Example Response

```json
{
  "predicted_class": "fresh_banana",
  "confidence": 0.9847,
  "freshness_status": "fresh",
  "crop_type": "banana",
  "quality_score": 96,
  "freshness_score": 99,
  "damage_score": 3,
  "ripeness_level": 93,
  "quality_grade": "A",
  "hindi_label": "ताज़ा केला",
  "top_predictions": [...],
  "recommendations": {
    "action": "sell",
    "english": "Your Banana is fresh and market-ready. Sell within 2-3 days for the best price.",
    "hindi": "आपका Banana ताज़ा है और बाज़ार के लिए तैयार है। सबसे अच्छे दाम के लिए 2-3 दिन में बेचें।"
  },
  "inference_time_ms": 45.2
}
```

## Teardown

```bash
python deploy_sagemaker.py --delete
```

## CloudFormation (Full Stack)

The model endpoint is also included in the full CloudFormation stack:

```bash
cd infra
./deploy.sh dev <db-password>
```

Resources created:
- `SageMakerExecutionRole` — IAM role for SageMaker
- `FreshnessModel` — SageMaker model pointing to S3 artifact
- `FreshnessEndpointConfig` — Serverless config (2 GB RAM, 5 max concurrency)
- `FreshnessEndpoint` — Live inference endpoint

## Backend Integration

The FastAPI backend (`quality_service.py`) automatically uses the SageMaker endpoint when the env var `SAGEMAKER_FRESHNESS_ENDPOINT` is set:

```
POST /api/v1/quality/assess
Content-Type: multipart/form-data

file: <image.jpg>
crop_name: banana
```

Inference hierarchy:
1. **SageMaker** (production) → `SAGEMAKER_FRESHNESS_ENDPOINT` env var
2. **Local ONNX** (development) → `models/freshness_v1_best.onnx`
3. **Local PyTorch** (development) → `models/freshness_v1_best.pth`
4. **Amazon Rekognition** (fallback) → generic label detection
5. **Simulated** (demo) → random realistic scores

## Cost Estimate

| Mode | Idle Cost | Per Inference | Notes |
|------|-----------|---------------|-------|
| Serverless | $0 | ~$0.0001 | Scales to zero, 1-2 min cold start |
| Real-time (ml.m5.large) | ~$0.115/hr | Included | Always warm, <100ms latency |
| Lambda + ONNX | $0 | ~$0.00005 | Alternative approach |

For the hackathon, **Serverless** is recommended — zero cost when not in use.

## Files

| File | Description |
|------|-------------|
| `sagemaker/deploy_sagemaker.py` | CLI deployment script |
| `sagemaker/inference_handler.py` | SageMaker inference handler (packaged in model.tar.gz) |
| `models/freshness_v1_best.onnx` | Exported ONNX model (0.3 MB) |
| `models/freshness_v1_best.pth` | PyTorch checkpoint (11.3 MB) |
| `models/model.tar.gz` | SageMaker model package |
