# SwadeshAI - Infrastructure Deployment Guide

## Prerequisites

### Required Tools
- AWS CLI v2
- Docker Desktop
- Python 3.11+
- Git

### AWS Account Setup
1. Create AWS account (or use existing)
2. Configure AWS CLI:
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region (ap-south-1), Output format (json)
```

3. Verify access:
```bash
aws sts get-caller-identity
```

### Required AWS Service Limits
- ECS Fargate: 10 tasks
- RDS: 1 instance
- DynamoDB: 5 tables
- S3: 3 buckets
- API Gateway: 1 REST API

## Deployment Options

### Option 1: CloudFormation (Recommended)

**Deploy full stack**:
```bash
cd infra
chmod +x deploy.sh
./deploy.sh dev YourSecurePassword123
```

**What it deploys**:
- VPC with public/private subnets
- ECS Fargate cluster + service
- RDS PostgreSQL database
- DynamoDB tables (4)
- S3 buckets (3)
- API Gateway
- Cognito User Pool
- CloudWatch logs
- IAM roles and policies

**Deployment time**: ~15-20 minutes

**Verify deployment**:
```bash
aws cloudformation describe-stacks --stack-name swadesh-ai-dev
```

### Option 2: Manual AWS Console Setup

#### Step 1: Create VPC
1. Go to VPC Console
2. Create VPC: `swadesh-ai-vpc` (10.0.0.0/16)
3. Create subnets:
   - Public: 10.0.1.0/24, 10.0.2.0/24
   - Private: 10.0.3.0/24, 10.0.4.0/24
4. Create Internet Gateway and attach to VPC
5. Create NAT Gateway in public subnet
6. Configure route tables

#### Step 2: Create RDS Database
1. Go to RDS Console
2. Create PostgreSQL database:
   - Engine: PostgreSQL 15
   - Instance: db.t3.medium
   - Storage: 100 GB GP3
   - Multi-AZ: Yes (production)
   - VPC: swadesh-ai-vpc
   - Subnets: Private subnets
   - Security group: Allow 5432 from ECS
3. Note the endpoint URL

#### Step 3: Create DynamoDB Tables
1. Go to DynamoDB Console
2. Create tables:
   - `swadesh-sessions` (session_id: String)
   - `swadesh-alerts` (user_id: String, timestamp: Number)
   - `swadesh-chat-history` (user_id: String, message_id: String)
   - `swadesh-market-prices` (crop_type: String, date: String)
3. Enable TTL on sessions and prices tables

#### Step 4: Create S3 Buckets
1. Go to S3 Console
2. Create buckets:
   - `swadesh-ai-images-dev`
   - `swadesh-ai-models-dev`
   - `swadesh-ai-logs-dev`
3. Enable versioning and encryption

#### Step 5: Create ECR Repository
1. Go to ECR Console
2. Create repository: `swadesh-ai/backend`
3. Enable scan on push

#### Step 6: Build and Push Docker Image
```bash
cd backend

# Build image
docker build -f Dockerfile.aws -t swadesh-ai:latest .

# Login to ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-south-1.amazonaws.com

# Tag image
docker tag swadesh-ai:latest <account-id>.dkr.ecr.ap-south-1.amazonaws.com/swadesh-ai:latest

# Push image
docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/swadesh-ai:latest
```

#### Step 7: Create ECS Cluster
1. Go to ECS Console
2. Create cluster: `swadesh-ai-cluster` (Fargate)
3. Create task definition:
   - Family: `swadesh-ai-backend`
   - Launch type: Fargate
   - CPU: 1 vCPU
   - Memory: 2 GB
   - Container: Use ECR image
   - Port: 8000
   - Environment variables: DB_HOST, AWS_REGION
   - Secrets: DB_PASSWORD from Secrets Manager
4. Create service:
   - Desired count: 2
   - Load balancer: Create new ALB
   - Target group: Port 8000
   - Health check: /api/v1/health

#### Step 8: Create API Gateway
1. Go to API Gateway Console
2. Create REST API: `swadesh-ai-api`
3. Create resources and methods
4. Integration: HTTP proxy to ALB
5. Deploy to stage: `v1`

#### Step 9: Create Cognito User Pool
1. Go to Cognito Console
2. Create user pool: `swadesh-ai-users`
3. Sign-in: Phone number
4. MFA: Optional
5. Create app client
6. Configure API Gateway authorizer

#### Step 10: Configure CloudFront (Optional)
1. Go to CloudFront Console
2. Create distribution
3. Origin: API Gateway domain
4. Behaviors: Cache settings
5. SSL certificate: Request from ACM

### Option 3: Terraform (Alternative)

**Deploy with Terraform**:
```bash
cd infra/terraform
terraform init
terraform plan -var="environment=dev" -var="db_password=YourPassword123"
terraform apply -auto-approve
```

## Post-Deployment Configuration

### 1. Initialize Database
```bash
# Connect to RDS
psql -h <rds-endpoint> -U swadesh_admin -d swadesh_ai

# Run initialization script
\i backend/init_db.sql
```

### 2. Upload ML Models to S3
```bash
aws s3 cp ml/models/ s3://swadesh-ai-models-dev/models/ --recursive
```

### 3. Configure Environment Variables
Update ECS task definition with:
```
DB_HOST=<rds-endpoint>
DB_NAME=swadesh_ai
DB_USER=swadesh_admin
AWS_REGION=ap-south-1
S3_BUCKET=swadesh-ai-images-dev
DYNAMODB_SESSIONS_TABLE=swadesh-sessions
DYNAMODB_ALERTS_TABLE=swadesh-alerts
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
```

### 4. Test Deployment
```bash
# Get ALB DNS name
aws elbv2 describe-load-balancers --names swadesh-ai-alb --query 'LoadBalancers[0].DNSName'

# Test health endpoint
curl https://<alb-dns>/api/v1/health

# Expected response:
# {"status": "healthy", "timestamp": "2026-03-08T..."}
```

### 5. Configure Android App
Update `android/app/src/main/java/com/swadesh/ai/data/api/RetrofitClient.kt`:
```kotlin
private const val BASE_URL = "https://<cloudfront-domain>/"
// or
private const val BASE_URL = "https://<api-gateway-domain>/"
```

## Monitoring Setup

### CloudWatch Alarms
```bash
# Create high CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name swadesh-high-cpu \
  --alarm-description "Alert when ECS CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions <sns-topic-arn>
```

### Log Insights Queries
```sql
-- API errors
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100

-- Slow requests
fields @timestamp, request_duration
| filter request_duration > 1000
| sort request_duration desc
```

## Scaling Configuration

### Auto Scaling Policies

#### ECS Service Scaling
```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/swadesh-ai-cluster/swadesh-ai-backend \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/swadesh-ai-cluster/swadesh-ai-backend \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

**scaling-policy.json**:
```json
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleInCooldown": 300,
  "ScaleOutCooldown": 60
}
```

## Backup & Recovery

### RDS Backup
```bash
# Create manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier swadesh-ai-db \
  --db-snapshot-identifier swadesh-ai-backup-$(date +%Y%m%d)

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier swadesh-ai-db-restored \
  --db-snapshot-identifier swadesh-ai-backup-20260308
```

### DynamoDB Backup
```bash
# Enable point-in-time recovery
aws dynamodb update-continuous-backups \
  --table-name swadesh-sessions \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

## Security Hardening

### 1. Enable AWS WAF
```bash
aws wafv2 create-web-acl \
  --name swadesh-ai-waf \
  --scope REGIONAL \
  --default-action Allow={} \
  --rules file://waf-rules.json
```

### 2. Enable GuardDuty
```bash
aws guardduty create-detector --enable
```

### 3. Enable CloudTrail
```bash
aws cloudtrail create-trail \
  --name swadesh-ai-audit \
  --s3-bucket-name swadesh-ai-logs-dev
```

## Cost Monitoring

### Set up Budget Alerts
```bash
aws budgets create-budget \
  --account-id <account-id> \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

**budget.json**:
```json
{
  "BudgetName": "SwadeshAI-Monthly",
  "BudgetLimit": {
    "Amount": "200",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

## Troubleshooting

### ECS Tasks Not Starting
```bash
# Check task logs
aws logs tail /ecs/swadesh-ai --follow

# Check task definition
aws ecs describe-task-definition --task-definition swadesh-ai-backend

# Check service events
aws ecs describe-services --cluster swadesh-ai-cluster --services swadesh-ai-backend
```

### RDS Connection Issues
```bash
# Test connectivity from ECS
aws ecs execute-command \
  --cluster swadesh-ai-cluster \
  --task <task-id> \
  --container backend \
  --interactive \
  --command "psql -h <rds-endpoint> -U swadesh_admin -d swadesh_ai"
```

### API Gateway 5XX Errors
```bash
# Check CloudWatch logs
aws logs tail /aws/apigateway/swadesh-ai-api --follow

# Check ALB target health
aws elbv2 describe-target-health --target-group-arn <target-group-arn>
```

## Cleanup

### Delete Stack
```bash
# CloudFormation
aws cloudformation delete-stack --stack-name swadesh-ai-dev

# Terraform
cd infra/terraform
terraform destroy -auto-approve
```

### Manual Cleanup
```bash
# Delete S3 buckets (must be empty first)
aws s3 rm s3://swadesh-ai-images-dev --recursive
aws s3 rb s3://swadesh-ai-images-dev

# Delete ECR images
aws ecr batch-delete-image \
  --repository-name swadesh-ai/backend \
  --image-ids imageTag=latest

# Delete CloudWatch logs
aws logs delete-log-group --log-group-name /ecs/swadesh-ai
```

## Production Checklist

- [ ] Enable Multi-AZ for RDS
- [ ] Enable CloudFront distribution
- [ ] Configure custom domain with Route 53
- [ ] Enable AWS WAF
- [ ] Set up CloudWatch alarms
- [ ] Enable automated backups
- [ ] Configure secrets rotation
- [ ] Enable X-Ray tracing
- [ ] Set up CI/CD pipeline
- [ ] Configure auto-scaling policies
- [ ] Enable GuardDuty
- [ ] Set up budget alerts
- [ ] Document runbooks
- [ ] Perform load testing
- [ ] Configure disaster recovery

## Support & Resources

- **AWS Documentation**: https://docs.aws.amazon.com
- **CloudFormation Template**: `infra/cloudformation/main-stack.yaml`
- **Deployment Script**: `infra/deploy.sh`
- **Architecture Diagram**: `docs/swadesh_ai_aws_architecture.png`

---

**Last Updated**: March 2026  
**Version**: 1.0
