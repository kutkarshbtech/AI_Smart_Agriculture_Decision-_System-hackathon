#!/usr/bin/env python3
"""
Deploy the SwadeshAI Freshness Detection model to AWS SageMaker.

Supports two endpoint types:
    1. Serverless  — pay-per-request, auto-scales to zero (hackathon default)
    2. Real-time   — always-on, sub-100ms latency

Architecture:
    ONNX model  →  S3 (model.tar.gz)  →  SageMaker Model  →  Endpoint

Prerequisites:
    - AWS CLI configured (`aws configure`)
    - boto3, sagemaker SDK installed
    - ONNX model exported at ml/freshness_detection/models/freshness_v1_best.onnx

Usage:
    # Serverless (recommended for hackathon — $0 when idle)
    python deploy_sagemaker.py --mode serverless

    # Real-time (always warm, ~$0.05/hr)
    python deploy_sagemaker.py --mode realtime

    # Delete the endpoint
    python deploy_sagemaker.py --delete

    # Test the endpoint
    python deploy_sagemaker.py --test --image ../samples/test_banana.jpg
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
MODEL_NAME = f"{PROJECT_NAME}-freshness-detector"
ENDPOINT_CONFIG_NAME = f"{MODEL_NAME}-config"
ENDPOINT_NAME = f"{MODEL_NAME}-endpoint"

REGION = os.environ.get("AWS_REGION", "ap-south-1")
S3_BUCKET = os.environ.get("SAGEMAKER_BUCKET", f"{PROJECT_NAME}-ml-models-dev")
S3_KEY = "models/freshness/model.tar.gz"

# SageMaker PyTorch Inference container (includes onnxruntime)
# Using PyTorch 2.1 CPU image — lightweight, fast cold-start
FRAMEWORK_VERSION = "2.1"
PY_VERSION = "py310"
INSTANCE_TYPE = "ml.m5.large"  # For real-time endpoint

# Serverless config
SERVERLESS_MEMORY_MB = 2048      # 2 GB (enough for MobileNetV2 ONNX)
SERVERLESS_MAX_CONCURRENCY = 5   # Max concurrent invocations

# Paths
SCRIPT_DIR = Path(__file__).parent
ML_DIR = SCRIPT_DIR.parent
MODELS_DIR = ML_DIR / "models"
ONNX_MODEL = MODELS_DIR / "freshness_v1_best.onnx"
CLASS_MAPPING = MODELS_DIR / "class_mapping.json"
INFERENCE_HANDLER = SCRIPT_DIR / "inference_handler.py"


def get_sagemaker_execution_role():
    """
    Get or create a SageMaker execution role.

    For local development, tries IAM; for SageMaker notebooks, uses
    the notebook role.
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

    # Create the role
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
        Description="SwadeshAI SageMaker execution role",
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

    # Wait for role propagation
    print("  Waiting for IAM role propagation (10s)...")
    time.sleep(10)

    return role_arn


def package_model() -> str:
    """
    Package the ONNX model + inference handler into model.tar.gz.

    SageMaker expects:
        model.tar.gz/
        ├── freshness_v1_best.onnx
        ├── class_mapping.json
        └── code/
            └── inference.py    ← SageMaker looks for code/inference.py
    """
    print("\n[1/4] Packaging model artifacts...")

    if not ONNX_MODEL.exists():
        print(f"  ✗ ONNX model not found at: {ONNX_MODEL}")
        print("    Run: python export_model.py --model models/freshness_v1_best.pth --format onnx")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Copy model
        shutil.copy2(ONNX_MODEL, tmpdir / "freshness_v1_best.onnx")
        print(f"  ✓ ONNX model: {ONNX_MODEL.stat().st_size / 1024:.0f} KB")

        # Copy class mapping if exists
        if CLASS_MAPPING.exists():
            shutil.copy2(CLASS_MAPPING, tmpdir / "class_mapping.json")
            print(f"  ✓ Class mapping: {CLASS_MAPPING.name}")

        # Create code/ directory with inference handler
        code_dir = tmpdir / "code"
        code_dir.mkdir()
        shutil.copy2(INFERENCE_HANDLER, code_dir / "inference.py")
        print(f"  ✓ Inference handler: code/inference.py")

        # Create requirements.txt for the container
        reqs = code_dir / "requirements.txt"
        reqs.write_text("onnxruntime>=1.16.0\nPillow>=10.0.0\nnumpy>=1.24.0\n")
        print(f"  ✓ Requirements: code/requirements.txt")

        # Create tar.gz
        tar_path = MODELS_DIR / "model.tar.gz"
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
        # Enable versioning
        s3.put_bucket_versioning(
            Bucket=S3_BUCKET,
            VersioningConfiguration={"Status": "Enabled"},
        )

    s3.upload_file(tar_path, S3_BUCKET, S3_KEY)
    print(f"  ✓ Uploaded to: {s3_uri}")

    return s3_uri


def create_sagemaker_model(s3_uri: str, role_arn: str) -> str:
    """Create a SageMaker Model resource."""
    print("\n[3/4] Creating SageMaker model...")

    sm = boto3.client("sagemaker", region_name=REGION)

    # Get the PyTorch inference container image URI
    image_uri = _get_pytorch_image_uri()

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
            {"Key": "ModelType", "Value": "freshness-detection"},
        ],
    )

    print(f"  ✓ Created model: {MODEL_NAME}")
    print(f"  ✓ Container: {image_uri}")
    return MODEL_NAME


def create_endpoint(mode: str = "serverless") -> str:
    """
    Create a SageMaker endpoint configuration and endpoint.

    Args:
        mode: "serverless" or "realtime"
    """
    print(f"\n[4/4] Creating SageMaker {mode} endpoint...")

    sm = boto3.client("sagemaker", region_name=REGION)

    # Delete existing endpoint config
    try:
        sm.delete_endpoint_config(EndpointConfigName=ENDPOINT_CONFIG_NAME)
    except ClientError:
        pass

    # Build endpoint config
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
        print(f"  Deleting old endpoint (waiting up to 5 min)...")
        waiter = sm.get_waiter("endpoint_deleted")
        waiter.wait(
            EndpointName=ENDPOINT_NAME,
            WaiterConfig={"Delay": 15, "MaxAttempts": 20},
        )
    except ClientError:
        pass

    # Create endpoint
    sm.create_endpoint(
        EndpointName=ENDPOINT_NAME,
        EndpointConfigName=ENDPOINT_CONFIG_NAME,
        Tags=[{"Key": "Project", "Value": PROJECT_NAME}],
    )

    print(f"  ✓ Endpoint creation started: {ENDPOINT_NAME}")
    print(f"  ⏳ Waiting for endpoint to become InService...")

    # Wait for endpoint
    waiter = sm.get_waiter("endpoint_in_service")
    try:
        waiter.wait(
            EndpointName=ENDPOINT_NAME,
            WaiterConfig={"Delay": 30, "MaxAttempts": 40},  # up to 20 min
        )
        print(f"  ✓ Endpoint is LIVE: {ENDPOINT_NAME}")
    except Exception as e:
        # Check status
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

    for name, delete_fn, desc in [
        (ENDPOINT_NAME, sm.delete_endpoint, "Endpoint"),
        (ENDPOINT_CONFIG_NAME, sm.delete_endpoint_config, "Endpoint config"),
        (MODEL_NAME, sm.delete_model, "Model"),
    ]:
        try:
            if desc == "Endpoint":
                delete_fn(EndpointName=name)
            elif desc == "Endpoint config":
                delete_fn(EndpointConfigName=name)
            else:
                delete_fn(ModelName=name)
            print(f"  ✓ Deleted {desc}: {name}")
        except ClientError as e:
            print(f"  - {desc} {name}: {e.response['Error']['Message']}")


def test_endpoint(image_path: str = None):
    """Test the live SageMaker endpoint with an image."""
    import base64

    runtime = boto3.client("sagemaker-runtime", region_name=REGION)

    if image_path:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        content_type = "image/jpeg"
        body = image_bytes
        print(f"\n  Testing with: {image_path}")
    else:
        # Generate a dummy test image
        from PIL import Image
        import io

        img = Image.new("RGB", (224, 224), color=(100, 200, 50))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        body = buf.getvalue()
        content_type = "image/jpeg"
        print("\n  Testing with: dummy 224×224 green image")

    print(f"  Invoking endpoint: {ENDPOINT_NAME}")
    start = time.time()

    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType=content_type,
        Body=body,
    )

    latency = round((time.time() - start) * 1000)
    result = json.loads(response["Body"].read().decode("utf-8"))

    print(f"\n  ═══════════════════════════════════════════════════════")
    print(f"  SageMaker CV Result  (computer-vision only)")
    print(f"  ═══════════════════════════════════════════════════════")
    print(f"  Prediction:    {result['predicted_class']}")
    print(f"  Confidence:    {result['confidence']:.1%}")
    print(f"  Status:        {result['freshness_status']}")
    print(f"  Crop:          {result['crop_type']}  ({result['hindi_label']})")
    print(f"  Quality Score: {result['quality_score']}  Grade: {result['quality_grade']}")
    print(f"  Freshness:     {result['freshness_score']}/100")
    print(f"  Damage:        {result['damage_score']}/100")
    print(f"  Ripeness:      {result['ripeness_level']}/100")
    print(f"  Latency:       {latency} ms (end-to-end)")
    print(f"  Model latency: {result['inference_time_ms']} ms")
    print(f"  ───────────────────────────────────────────────────────")
    print(f"  Bedrock context (pass this to Claude for insights):")
    for line in result["bedrock_context"].splitlines():
        print(f"    {line}")
    print(f"  ═══════════════════════════════════════════════════════")
    print(f"\n  Next step — get Bedrock insights:")
    print(f"    from bedrock_freshness_insights import get_freshness_insights")
    print(f"    insights = get_freshness_insights(result)")
    print(f"    print(insights['english']['summary'])")


def _get_pytorch_image_uri() -> str:
    """
    Get the SageMaker PyTorch inference container URI for the current region.

    Uses the DLC (Deep Learning Container) registry.
    """
    # SageMaker DLC account IDs per region
    # https://docs.aws.amazon.com/sagemaker/latest/dg/pre-built-containers-frameworks-deep-learning.html
    account_map = {
        "ap-south-1": "763104351884",
        "us-east-1": "763104351884",
        "us-west-2": "763104351884",
        "eu-west-1": "763104351884",
        "ap-southeast-1": "763104351884",
    }

    account = account_map.get(REGION, "763104351884")
    return (
        f"{account}.dkr.ecr.{REGION}.amazonaws.com/"
        f"pytorch-inference:{FRAMEWORK_VERSION}-cpu-{PY_VERSION}-ubuntu20.04-sagemaker"
    )


def print_summary():
    """Print deployment summary and usage instructions."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              SwadeshAI Freshness Model — Deployed           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Endpoint:  {ENDPOINT_NAME:<44}  ║
║  Region:    {REGION:<44}  ║
║  S3 Model:  s3://{S3_BUCKET}/{S3_KEY:<22}  ║
║                                                              ║
║  Test with:                                                  ║
║    python deploy_sagemaker.py --test --image photo.jpg       ║
║                                                              ║
║  From Python:                                                ║
║    import boto3                                              ║
║    runtime = boto3.client('sagemaker-runtime')               ║
║    response = runtime.invoke_endpoint(                       ║
║        EndpointName='{ENDPOINT_NAME}',         ║
║        ContentType='image/jpeg',                             ║
║        Body=open('photo.jpg', 'rb').read()                   ║
║    )                                                         ║
║                                                              ║
║  Delete:                                                     ║
║    python deploy_sagemaker.py --delete                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def main():
    parser = argparse.ArgumentParser(
        description="Deploy SwadeshAI Freshness Model to SageMaker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode", choices=["serverless", "realtime"], default="serverless",
        help="Endpoint type (default: serverless — pay-per-request)",
    )
    parser.add_argument("--delete", action="store_true", help="Delete the endpoint")
    parser.add_argument("--test", action="store_true", help="Test the endpoint")
    parser.add_argument("--image", type=str, help="Image path for --test")
    parser.add_argument("--region", type=str, default=REGION, help="AWS region")
    parser.add_argument("--bucket", type=str, default=S3_BUCKET, help="S3 bucket for model")
    args = parser.parse_args()

    global REGION, S3_BUCKET
    REGION = args.region
    S3_BUCKET = args.bucket

    if args.delete:
        print("Deleting SageMaker resources...")
        delete_endpoint()
        return

    if args.test:
        test_endpoint(args.image)
        return

    print("=" * 60)
    print("  SwadeshAI — Freshness Detection Model → SageMaker")
    print(f"  Mode:   {args.mode}")
    print(f"  Region: {REGION}")
    print("=" * 60)

    # Step 1: Package
    tar_path = package_model()

    # Step 2: Upload to S3
    s3_uri = upload_to_s3(tar_path)

    # Step 3: Get/create IAM role
    print("\n[2.5] Setting up IAM role...")
    role_arn = get_sagemaker_execution_role()

    # Step 4: Create SageMaker model
    create_sagemaker_model(s3_uri, role_arn)

    # Step 5: Create endpoint
    create_endpoint(args.mode)

    # Summary
    print_summary()


if __name__ == "__main__":
    main()
