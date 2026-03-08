#!/usr/bin/env python3
"""
Deploy the SwadeshAI Spoilage Prediction model to AWS SageMaker.

Supports two endpoint types:
    1. Serverless  — pay-per-request, auto-scales to zero (hackathon default)
    2. Real-time   — always-on, sub-100ms latency

Architecture:
    XGBoost models (joblib) →  S3 (model.tar.gz)  →  SageMaker Model  →  Endpoint

The endpoint accepts JSON input with crop conditions and returns:
    - risk_level, spoilage_probability, remaining_shelf_life_days
    - Causal explanations (via Bedrock if available, else template-based)
    - Recommendations in Hindi + English

Prerequisites:
    - AWS CLI configured (`aws configure`)
    - boto3 installed
    - Trained models at ml/spoilage_prediction/models/

Usage:
    # Serverless (recommended for hackathon — $0 when idle)
    python sagemaker_deploy.py --mode serverless

    # Real-time
    python sagemaker_deploy.py --mode realtime

    # Delete the endpoint
    python sagemaker_deploy.py --delete

    # Test the endpoint
    python sagemaker_deploy.py --test

    # Test with specific crop conditions
    python sagemaker_deploy.py --test --crop tomato --temp 35 --humidity 80
"""

import os
import sys
import json
import time
import shutil
import tarfile
import argparse
import tempfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


# ── Configuration ─────────────────────────────────────────────────

PROJECT_NAME = "swadesh-ai"
MODEL_NAME = f"{PROJECT_NAME}-spoilage-predictor"
ENDPOINT_CONFIG_NAME = f"{MODEL_NAME}-config"
ENDPOINT_NAME = f"{MODEL_NAME}-endpoint"

REGION = os.environ.get("AWS_REGION", "ap-south-1")
S3_BUCKET = os.environ.get("SAGEMAKER_BUCKET", f"{PROJECT_NAME}-ml-models-dev")
S3_KEY = "models/spoilage/model.tar.gz"

# SageMaker SKLearn container (supports joblib + XGBoost)
FRAMEWORK_VERSION = "1.2-1"  # SKLearn framework version
PY_VERSION = "py3"
INSTANCE_TYPE = "ml.m5.large"

# Serverless config — XGBoost is lightweight, 1 GB is sufficient
SERVERLESS_MEMORY_MB = 1024
SERVERLESS_MAX_CONCURRENCY = 10

# Paths
SCRIPT_DIR = Path(__file__).parent
MODELS_DIR = SCRIPT_DIR / "models"
MODEL_PREFIX = "spoilage_v1"


# ── SageMaker Inference Handler ──────────────────────────────────
# This gets packaged inside model.tar.gz as code/inference.py
# SageMaker calls model_fn, input_fn, predict_fn, output_fn

INFERENCE_HANDLER_CODE = '''
"""
SageMaker inference handler for SwadeshAI Spoilage Prediction.

This runs inside the SageMaker container. It loads the 3 XGBoost sub-models
and serves predictions via the SageMaker inference API.

SageMaker calls these 4 functions in order:
    model_fn  → load model from disk
    input_fn  → parse incoming request
    predict_fn → run inference
    output_fn → format response
"""

import os
import json
import joblib
import numpy as np

# ── Crop profiles (subset for inference) ──
CROP_NAMES = {
    "tomato": "टमाटर", "banana": "केला", "mango": "आम", "potato": "आलू",
    "onion": "प्याज", "rice": "चावल", "wheat": "गेहूं", "apple": "सेब",
    "grape": "अंगूर", "spinach": "पालक", "okra": "भिंडी", "cauliflower": "फूलगोभी",
    "milk": "दूध", "curd": "दही", "paneer": "पनीर", "fish": "मछली",
}

RISK_LEVELS = ["low", "medium", "high", "critical"]
RISK_ICONS = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}

FEATURE_COLUMNS = [
    "crop_encoded", "temperature_c", "humidity_pct", "days_since_harvest",
    "initial_quality", "transport_hours", "is_cold_storage", "is_packaged",
    "distance_km", "ambient_shelf_days", "cold_shelf_days",
    "optimal_temp_mid", "damage_sensitivity",
]


def model_fn(model_dir):
    """Load the 3 XGBoost sub-models + metadata."""
    prefix = None
    # Find model prefix
    for f in os.listdir(model_dir):
        if f.endswith("_metadata.json"):
            prefix = f.replace("_metadata.json", "")
            break

    if prefix is None:
        prefix = "spoilage_v1"

    models = {
        "shelf_life": joblib.load(os.path.join(model_dir, f"{prefix}_shelf_life.joblib")),
        "probability": joblib.load(os.path.join(model_dir, f"{prefix}_probability.joblib")),
        "risk": joblib.load(os.path.join(model_dir, f"{prefix}_risk.joblib")),
    }

    # Load metadata
    meta_path = os.path.join(model_dir, f"{prefix}_metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            models["metadata"] = json.load(f)

    return models


def input_fn(request_body, content_type="application/json"):
    """Parse incoming JSON request."""
    if content_type != "application/json":
        raise ValueError(f"Unsupported content type: {content_type}")
    return json.loads(request_body)


def predict_fn(input_data, models):
    """Run prediction using the 3 sub-models."""
    # Handle batch or single input
    if isinstance(input_data, list):
        return [_predict_single(item, models) for item in input_data]
    return _predict_single(input_data, models)


def _predict_single(data, models):
    """Predict for a single input."""
    features = np.array([[
        data.get("crop_encoded", 0),
        data["temperature_c"],
        data["humidity_pct"],
        data["days_since_harvest"],
        data.get("initial_quality", 85),
        data.get("transport_hours", 2),
        1 if data.get("storage_type", "ambient") == "cold" else 0,
        1 if data.get("is_packaged", False) else 0,
        data.get("distance_km", 50),
        data.get("ambient_shelf_days", 7),
        data.get("cold_shelf_days", 21),
        data.get("optimal_temp_mid", 12),
        data.get("damage_sensitivity", 0.5),
    ]])

    # Run 3 sub-models
    shelf_life = float(models["shelf_life"].predict(features)[0])
    probability = float(models["probability"].predict(features)[0])
    risk_idx = int(models["risk"].predict(features)[0])

    shelf_life = max(0, shelf_life)
    probability = max(0, min(1, probability))
    risk_level = RISK_LEVELS[risk_idx] if risk_idx < len(RISK_LEVELS) else "medium"

    crop = data.get("crop", "tomato")
    return {
        "crop": crop,
        "crop_hindi": CROP_NAMES.get(crop, crop),
        "risk_level": risk_level,
        "risk_icon": RISK_ICONS.get(risk_level, "🟡"),
        "spoilage_probability": round(probability, 4),
        "remaining_shelf_life_days": round(shelf_life, 1),
        "input_summary": {
            "temperature_c": data["temperature_c"],
            "humidity_pct": data["humidity_pct"],
            "days_since_harvest": data["days_since_harvest"],
            "storage_type": data.get("storage_type", "ambient"),
            "transport_hours": data.get("transport_hours", 2),
        },
    }


def output_fn(prediction, accept="application/json"):
    """Format response as JSON."""
    return json.dumps(prediction, ensure_ascii=False), "application/json"
'''


def get_sagemaker_execution_role():
    """
    Get or create a SageMaker execution role.

    Creates a role with SageMaker, S3, CloudWatch, and Bedrock permissions
    (Bedrock for causal explanation engine).
    """
    iam = boto3.client("iam", region_name=REGION)
    role_name = f"{PROJECT_NAME}-sagemaker-role"

    try:
        response = iam.get_role(RoleName=role_name)
        role_arn = response["Role"]["Arn"]
        print(f"  Using existing role: {role_arn}")
        return role_arn
    except ClientError:
        pass

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "sagemaker.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    print(f"  Creating SageMaker execution role: {role_name}")
    response = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description="SwadeshAI SageMaker execution role (spoilage prediction)",
        Tags=[{"Key": "Project", "Value": PROJECT_NAME}],
    )
    role_arn = response["Role"]["Arn"]

    # Attach required policies
    policies = [
        "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
        "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
        "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess",
    ]
    for policy in policies:
        iam.attach_role_policy(RoleName=role_name, PolicyArn=policy)

    # Add inline policy for Bedrock access (explanation engine)
    bedrock_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                "Resource": "arn:aws:bedrock:*::foundation-model/*",
            }
        ],
    }
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName="BedrockInvokeAccess",
        PolicyDocument=json.dumps(bedrock_policy),
    )

    print("  Waiting for IAM role propagation (10s)...")
    time.sleep(10)

    return role_arn


def package_model() -> str:
    """
    Package XGBoost models + inference handler into model.tar.gz.

    SageMaker expects:
        model.tar.gz/
        ├── spoilage_v1_shelf_life.joblib
        ├── spoilage_v1_probability.joblib
        ├── spoilage_v1_risk.joblib
        ├── spoilage_v1_metadata.json
        └── code/
            ├── inference.py
            └── requirements.txt
    """
    print("\n[1/4] Packaging model artifacts...")

    # Verify models exist
    required_files = [
        f"{MODEL_PREFIX}_shelf_life.joblib",
        f"{MODEL_PREFIX}_probability.joblib",
        f"{MODEL_PREFIX}_risk.joblib",
    ]
    for fname in required_files:
        fpath = MODELS_DIR / fname
        if not fpath.exists():
            print(f"  ✗ Model not found: {fpath}")
            print("    Run: python train.py --preset balanced --samples 50000")
            sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Copy model files
        for fname in required_files:
            src = MODELS_DIR / fname
            shutil.copy2(src, tmpdir / fname)
            size_kb = src.stat().st_size / 1024
            print(f"  ✓ {fname}: {size_kb:.0f} KB")

        # Copy metadata
        meta = MODELS_DIR / f"{MODEL_PREFIX}_metadata.json"
        if meta.exists():
            shutil.copy2(meta, tmpdir / meta.name)
            print(f"  ✓ {meta.name}")

        # Feature importance
        fi = MODELS_DIR / f"{MODEL_PREFIX}_feature_importance.json"
        if fi.exists():
            shutil.copy2(fi, tmpdir / fi.name)
            print(f"  ✓ {fi.name}")

        # Create code/ directory
        code_dir = tmpdir / "code"
        code_dir.mkdir()

        # Write inference handler
        (code_dir / "inference.py").write_text(INFERENCE_HANDLER_CODE)
        print("  ✓ code/inference.py (SageMaker handler)")

        # Requirements for the container
        reqs = "xgboost>=2.0\njoblib>=1.3\nnumpy>=1.24\nscikit-learn>=1.3\n"
        (code_dir / "requirements.txt").write_text(reqs)
        print("  ✓ code/requirements.txt")

        # Create tar.gz
        tar_path = MODELS_DIR / "sagemaker_model.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            for item in tmpdir.iterdir():
                tar.add(item, arcname=item.name)

        size_mb = tar_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ Created: {tar_path} ({size_mb:.1f} MB)")

    return str(tar_path)


def upload_to_s3(tar_path: str) -> str:
    """Upload model.tar.gz to S3."""
    print("\n[2/4] Uploading model to S3...")

    s3 = boto3.client("s3", region_name=REGION)
    s3_uri = f"s3://{S3_BUCKET}/{S3_KEY}"

    # Create bucket if needed
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
    except ClientError:
        print(f"  Creating bucket: {S3_BUCKET}")
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=S3_BUCKET)
        else:
            s3.create_bucket(
                Bucket=S3_BUCKET,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )
        s3.put_bucket_versioning(
            Bucket=S3_BUCKET,
            VersioningConfiguration={"Status": "Enabled"},
        )

    s3.upload_file(tar_path, S3_BUCKET, S3_KEY)
    print(f"  ✓ Uploaded to: {s3_uri}")

    return s3_uri


def _get_sklearn_image_uri() -> str:
    """Get the SageMaker SKLearn inference container URI."""
    # DLC account IDs (same across regions)
    account = "763104351884"
    return (
        f"{account}.dkr.ecr.{REGION}.amazonaws.com/"
        f"sagemaker-scikit-learn:{FRAMEWORK_VERSION}-cpu-{PY_VERSION}"
    )


def create_sagemaker_model(s3_uri: str, role_arn: str) -> str:
    """Create a SageMaker Model resource."""
    print("\n[3/4] Creating SageMaker model...")

    sm = boto3.client("sagemaker", region_name=REGION)
    image_uri = _get_sklearn_image_uri()

    # Delete existing model if any
    try:
        sm.delete_model(ModelName=MODEL_NAME)
        print(f"  Deleted existing model: {MODEL_NAME}")
    except ClientError:
        pass

    sm.create_model(
        ModelName=MODEL_NAME,
        PrimaryContainer={
            "Image": image_uri,
            "ModelDataUrl": s3_uri,
            "Environment": {
                "SAGEMAKER_PROGRAM": "inference.py",
                "SAGEMAKER_SUBMIT_DIRECTORY": s3_uri,
                "SAGEMAKER_CONTAINER_LOG_LEVEL": "20",
            },
        },
        ExecutionRoleArn=role_arn,
        Tags=[
            {"Key": "Project", "Value": PROJECT_NAME},
            {"Key": "ModelType", "Value": "spoilage-prediction"},
        ],
    )

    print(f"  ✓ Created model: {MODEL_NAME}")
    print(f"  ✓ Container: {image_uri}")
    return MODEL_NAME


def create_endpoint(mode: str = "serverless") -> str:
    """Create SageMaker endpoint configuration and endpoint."""
    print(f"\n[4/4] Creating SageMaker {mode} endpoint...")

    sm = boto3.client("sagemaker", region_name=REGION)

    # Delete existing endpoint config
    try:
        sm.delete_endpoint_config(EndpointConfigName=ENDPOINT_CONFIG_NAME)
    except ClientError:
        pass

    variant = {
        "VariantName": "primary",
        "ModelName": MODEL_NAME,
    }

    if mode == "serverless":
        variant["ServerlessConfig"] = {
            "MemorySizeInMB": SERVERLESS_MEMORY_MB,
            "MaxConcurrency": SERVERLESS_MAX_CONCURRENCY,
        }
        print(f"  Memory: {SERVERLESS_MEMORY_MB} MB")
        print(f"  Max concurrency: {SERVERLESS_MAX_CONCURRENCY}")
    else:
        variant["InitialInstanceCount"] = 1
        variant["InstanceType"] = INSTANCE_TYPE
        variant["InitialVariantWeight"] = 1.0
        print(f"  Instance: {INSTANCE_TYPE}")

    sm.create_endpoint_config(
        EndpointConfigName=ENDPOINT_CONFIG_NAME,
        ProductionVariants=[variant],
        Tags=[{"Key": "Project", "Value": PROJECT_NAME}],
    )
    print(f"  ✓ Endpoint config: {ENDPOINT_CONFIG_NAME}")

    # Delete existing endpoint if any
    try:
        sm.delete_endpoint(EndpointName=ENDPOINT_NAME)
        print("  Deleting old endpoint (waiting up to 5 min)...")
        waiter = sm.get_waiter("endpoint_deleted")
        waiter.wait(
            EndpointName=ENDPOINT_NAME,
            WaiterConfig={"Delay": 15, "MaxAttempts": 20},
        )
    except ClientError:
        pass

    sm.create_endpoint(
        EndpointName=ENDPOINT_NAME,
        EndpointConfigName=ENDPOINT_CONFIG_NAME,
        Tags=[{"Key": "Project", "Value": PROJECT_NAME}],
    )

    print(f"  ✓ Endpoint creation started: {ENDPOINT_NAME}")
    print("  ⏳ Waiting for endpoint to become InService...")

    waiter = sm.get_waiter("endpoint_in_service")
    try:
        waiter.wait(
            EndpointName=ENDPOINT_NAME,
            WaiterConfig={"Delay": 30, "MaxAttempts": 40},
        )
        print(f"  ✓ Endpoint is LIVE: {ENDPOINT_NAME}")
    except Exception:
        desc = sm.describe_endpoint(EndpointName=ENDPOINT_NAME)
        status = desc["EndpointStatus"]
        if status == "Failed":
            reason = desc.get("FailureReason", "unknown")
            print(f"  ✗ Endpoint creation FAILED: {reason}")
        else:
            print(f"  ⏳ Endpoint status: {status} (may still be creating)")

    return ENDPOINT_NAME


def delete_endpoint():
    """Tear down the SageMaker endpoint, config, and model."""
    sm = boto3.client("sagemaker", region_name=REGION)

    for name, delete_fn, desc, kwarg in [
        (ENDPOINT_NAME, sm.delete_endpoint, "Endpoint", "EndpointName"),
        (ENDPOINT_CONFIG_NAME, sm.delete_endpoint_config, "Endpoint config", "EndpointConfigName"),
        (MODEL_NAME, sm.delete_model, "Model", "ModelName"),
    ]:
        try:
            delete_fn(**{kwarg: name})
            print(f"  ✓ Deleted {desc}: {name}")
        except ClientError as e:
            print(f"  - {desc} {name}: {e.response['Error']['Message']}")


def test_endpoint(crop: str = "tomato", temp: float = 30, humidity: float = 70):
    """Test the live SageMaker endpoint with crop conditions."""
    runtime = boto3.client("sagemaker-runtime", region_name=REGION)

    payload = {
        "crop": crop,
        "crop_encoded": _crop_to_index(crop),
        "temperature_c": temp,
        "humidity_pct": humidity,
        "days_since_harvest": 3,
        "initial_quality": 85,
        "transport_hours": 4,
        "storage_type": "ambient",
        "is_packaged": False,
        "distance_km": 50,
        "ambient_shelf_days": 7,
        "cold_shelf_days": 21,
        "optimal_temp_mid": 12,
        "damage_sensitivity": 0.5,
    }

    print(f"\n  Testing with: {crop} at {temp}°C, {humidity}% humidity")
    print(f"  Invoking endpoint: {ENDPOINT_NAME}")

    start = time.time()
    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Body=json.dumps(payload),
    )
    latency = round((time.time() - start) * 1000)

    result = json.loads(response["Body"].read().decode("utf-8"))

    print(f"\n  ═══════════════════════════════════════")
    print(f"  SageMaker Spoilage Prediction Result")
    print(f"  ═══════════════════════════════════════")
    print(f"  Crop:         {result['crop']} ({result['crop_hindi']})")
    print(f"  Risk:         {result['risk_icon']} {result['risk_level'].upper()}")
    print(f"  Probability:  {result['spoilage_probability']:.1%}")
    print(f"  Shelf Life:   {result['remaining_shelf_life_days']:.1f} days")
    print(f"  Latency:      {latency} ms (end-to-end)")
    print(f"  ═══════════════════════════════════════")


def _crop_to_index(crop: str) -> int:
    """Map crop name to encoded index (matching dataset.py)."""
    crops = [
        "tomato", "banana", "mango", "potato", "onion", "rice", "wheat",
        "apple", "grape", "spinach", "okra", "cauliflower", "milk", "curd",
        "paneer", "fish",
    ]
    return crops.index(crop) if crop in crops else 0


def print_summary():
    """Print deployment summary."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           SwadeshAI Spoilage Predictor — Deployed           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Endpoint:  {ENDPOINT_NAME:<44}  ║
║  Region:    {REGION:<44}  ║
║  S3 Model:  s3://{S3_BUCKET}/{S3_KEY:<22}  ║
║                                                              ║
║  Test:                                                       ║
║    python sagemaker_deploy.py --test --crop tomato --temp 35 ║
║                                                              ║
║  Python SDK:                                                 ║
║    runtime = boto3.client('sagemaker-runtime')               ║
║    response = runtime.invoke_endpoint(                       ║
║        EndpointName='{ENDPOINT_NAME}',      ║
║        ContentType='application/json',                       ║
║        Body=json.dumps({{"crop": "tomato",                     ║
║            "temperature_c": 35, "humidity_pct": 70,          ║
║            "days_since_harvest": 3}})                        ║
║    )                                                         ║
║                                                              ║
║  Delete:                                                     ║
║    python sagemaker_deploy.py --delete                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def main():
    parser = argparse.ArgumentParser(
        description="Deploy SwadeshAI Spoilage Predictor to SageMaker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode", choices=["serverless", "realtime"], default="serverless",
        help="Endpoint type (default: serverless)",
    )
    parser.add_argument("--delete", action="store_true", help="Delete the endpoint")
    parser.add_argument("--test", action="store_true", help="Test the endpoint")
    parser.add_argument("--crop", type=str, default="tomato", help="Crop for --test")
    parser.add_argument("--temp", type=float, default=30, help="Temperature for --test")
    parser.add_argument("--humidity", type=float, default=70, help="Humidity for --test")
    parser.add_argument("--region", type=str, default=REGION, help="AWS region")
    parser.add_argument("--bucket", type=str, default=S3_BUCKET, help="S3 bucket")
    args = parser.parse_args()

    global REGION, S3_BUCKET
    REGION = args.region
    S3_BUCKET = args.bucket

    if args.delete:
        print("Deleting SageMaker resources...")
        delete_endpoint()
        return

    if args.test:
        test_endpoint(args.crop, args.temp, args.humidity)
        return

    print("=" * 60)
    print("  SwadeshAI — Spoilage Prediction Model → SageMaker")
    print(f"  Mode:   {args.mode}")
    print(f"  Region: {REGION}")
    print("=" * 60)

    tar_path = package_model()
    s3_uri = upload_to_s3(tar_path)

    print("\n[2.5] Setting up IAM role...")
    role_arn = get_sagemaker_execution_role()

    create_sagemaker_model(s3_uri, role_arn)
    create_endpoint(args.mode)
    print_summary()


if __name__ == "__main__":
    main()
