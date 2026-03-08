#!/bin/bash
# SwadeshAI — Deploy script for AWS infrastructure
# Usage: ./deploy.sh <environment> <db-password> [mandi-api-key]

set -euo pipefail

ENVIRONMENT="${1:-dev}"
DB_PASSWORD="${2:?Usage: ./deploy.sh <environment> <db-password> [mandi-api-key]}"
MANDI_API_KEY="${3:-}"
PROJECT_NAME="swadesh-ai"
REGION="ap-south-1"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
ML_BUCKET_NAME="${PROJECT_NAME}-ml-models-${ENVIRONMENT}"

echo "========================================="
echo "  SwadeshAI Infrastructure Deployment"
echo "  Environment: ${ENVIRONMENT}"
echo "  Region: ${REGION}"
echo "  AWS_ONLY: true (no local fallbacks)"
echo "========================================="

# Step 1: Validate template
echo "[1/7] Validating CloudFormation template..."
aws cloudformation validate-template \
    --template-body file://infra/cloudformation/main-stack.yaml \
    --region ${REGION}

# Step 2: Pre-create S3 bucket & upload ML model (needed before SageMaker)
echo "[2/7] Preparing S3 bucket and ML model..."
# Create bucket if it doesn't exist
aws s3 mb "s3://${ML_BUCKET_NAME}" --region ${REGION} 2>/dev/null || true

if [ -f "ml/freshness_detection/models/model.tar.gz" ]; then
    aws s3 cp ml/freshness_detection/models/model.tar.gz \
        "s3://${ML_BUCKET_NAME}/models/freshness/model.tar.gz" \
        --region ${REGION}
    echo "Freshness model uploaded to s3://${ML_BUCKET_NAME}/models/freshness/model.tar.gz"
else
    echo "WARNING: ml/freshness_detection/models/model.tar.gz not found."
    echo "  SageMaker endpoint will fail. Run this first:"
    echo "  cd ml/freshness_detection && tar -czf models/model.tar.gz ..."
fi

# Step 3: Deploy/Update CloudFormation stack
echo "[3/7] Deploying CloudFormation stack..."
PARAMS="Environment=${ENVIRONMENT} ProjectName=${PROJECT_NAME} DBPassword=${DB_PASSWORD}"
if [ -n "${MANDI_API_KEY}" ]; then
    PARAMS="${PARAMS} MandiApiKey=${MANDI_API_KEY}"
fi

aws cloudformation deploy \
    --template-file infra/cloudformation/main-stack.yaml \
    --stack-name ${STACK_NAME} \
    --parameter-overrides ${PARAMS} \
    --capabilities CAPABILITY_NAMED_IAM \
    --region ${REGION} \
    --no-fail-on-empty-changeset

# Step 4: Get outputs
echo "[4/7] Retrieving stack outputs..."
aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs' \
    --output table

# Step 5: Build and push Docker image
echo "[5/7] Building and pushing backend Docker image..."
ECR_URI=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query "Stacks[0].Outputs[?OutputKey=='BackendECRUri'].OutputValue" \
    --output text)

if [ -n "${ECR_URI}" ]; then
    # Login to ECR
    aws ecr get-login-password --region ${REGION} | \
        docker login --username AWS --password-stdin "${ECR_URI%%/*}"

    # Build and push (use slim AWS Dockerfile — no torch/onnx)
    docker build -f backend/Dockerfile.aws -t ${PROJECT_NAME}-backend backend/
    docker tag ${PROJECT_NAME}-backend:latest ${ECR_URI}:latest
    docker push ${ECR_URI}:latest
    echo "Backend image pushed to ${ECR_URI}:latest"
fi

# Step 6: Scale up ECS service (starts with 0 tasks until image is pushed)
echo "[6/7] Scaling ECS service to 1 task..."
CLUSTER_NAME=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query "Stacks[0].Outputs[?OutputKey=='ECSClusterName'].OutputValue" \
    --output text)

aws ecs update-service \
    --cluster ${CLUSTER_NAME} \
    --service ${PROJECT_NAME}-backend-${ENVIRONMENT} \
    --desired-count 1 \
    --force-new-deployment \
    --region ${REGION}

# Step 7: Print the public endpoint
echo "[7/7] Verifying deployment..."
BACKEND_URL=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query "Stacks[0].Outputs[?OutputKey=='BackendEndpoint'].OutputValue" \
    --output text)

echo ""
echo "========================================="
echo "  Deployment Complete!"
echo "  Backend URL: ${BACKEND_URL}"
echo "  Health Check: ${BACKEND_URL}/api/v1/health"
echo "  API Docs: ${BACKEND_URL}/docs"
echo ""
echo "  Test with:"
echo "    ./scripts/test_aws_endpoint.sh ${BACKEND_URL}"
echo "========================================="
