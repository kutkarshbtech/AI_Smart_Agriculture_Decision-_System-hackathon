# SwadeshAI - AWS Architecture Documentation

## Overview

SwadeshAI is deployed on AWS using a cloud-native, microservices-based architecture designed for scalability, reliability, and cost-effectiveness. The platform leverages multiple AWS AI/ML services to provide intelligent post-harvest decision support for farmers.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Client Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Android    │  │   Web App    │  │   Mobile     │         │
│  │     App      │  │  (React/Vue) │  │   Browser    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │ HTTPS
          ┌──────────────────▼──────────────────┐
          │      Amazon CloudFront (CDN)        │
          │    - Global edge caching            │
          │    - SSL/TLS termination            │
          │    - DDoS protection (Shield)       │
          └──────────────────┬──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │      Amazon API Gateway             │
          │    - REST API management            │
          │    - Request throttling             │
          │    - API key management             │
          │    - CORS configuration             │
          └──────────────────┬──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │      Amazon Cognito                 │
          │    - Phone-based OTP auth           │
          │    - User pool management           │
          │    - JWT token generation           │
          └──────────────────┬──────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│              Application Layer (ECS Fargate)            │
│  ┌──────────────────────────────────────────────────┐  │
│  │         FastAPI Backend Container                │  │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────┐ │  │
│  │  │  Spoilage  │  │  Pricing   │  │  Quality  │ │  │
│  │  │  Service   │  │  Service   │  │  Service  │ │  │
│  │  └────────────┘  └────────────┘  └───────────┘ │  │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────┐ │  │
│  │  │   Buyer    │  │  Chatbot   │  │  Weather  │ │  │
│  │  │  Matching  │  │  Service   │  │  Service  │ │  │
│  │  └────────────┘  └────────────┘  └───────────┘ │  │
│  │  ┌────────────┐  ┌────────────┐                │  │
│  │  │   Alert    │  │ Dashboard  │                │  │
│  │  │  Service   │  │  Service   │                │  │
│  │  └────────────┘  └────────────┘                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Application Load Balancer                │  │
│  │    - Health checks                               │  │
│  │    - Auto-scaling triggers                       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
┌─────────▼─────────┐              ┌───────────▼──────────┐
│   AWS AI/ML       │              │   Data Layer         │
│   Services        │              │                      │
│                   │              │                      │
│ ┌───────────────┐ │              │ ┌────────────────┐  │
│ │   Bedrock     │ │              │ │  RDS PostgreSQL│  │
│ │   (Claude)    │ │              │ │  - Users       │  │
│ │   Chatbot     │ │              │ │  - Batches     │  │
│ └───────────────┘ │              │ │  - Transactions│  │
│                   │              │ └────────────────┘  │
│ ┌───────────────┐ │              │                      │
│ │ Rekognition   │ │              │ ┌────────────────┐  │
│ │ Image Quality │ │              │ │   DynamoDB     │  │
│ │ Assessment    │ │              │ │  - Sessions    │  │
│ └───────────────┘ │              │ │  - Alerts      │  │
│                   │              │ │  - Chat logs   │  │
│ ┌───────────────┐ │              │ │  - Prices      │  │
│ │  SageMaker    │ │              │ └────────────────┘  │
│ │  ML Models    │ │              │                      │
│ │  (Optional)   │ │              │ ┌────────────────┐  │
│ └───────────────┘ │              │ │   Amazon S3    │  │
│                   │              │ │  - Crop images │  │
│ ┌───────────────┐ │              │ │  - ML models   │  │
│ │   Lambda      │ │              │ │  - Logs        │  │
│ │  Functions    │ │              │ └────────────────┘  │
│ │  (Inference)  │ │              │                      │
│ └───────────────┘ │              │ ┌────────────────┐  │
│                   │              │ │  Neptune       │  │
│ ┌───────────────┐ │              │ │  Knowledge     │  │
│ │   Location    │ │              │ │  Graph         │  │
│ │   Service     │ │              │ │  (Optional)    │  │
│ │  Geo-matching │ │              │ └────────────────┘  │
│ └───────────────┘ │              └──────────────────────┘
└───────────────────┘
          │
┌─────────▼─────────┐
│  Notification     │
│  Services         │
│                   │
│ ┌───────────────┐ │
│ │     SNS       │ │
│ │  SMS Alerts   │ │
│ └───────────────┘ │
│                   │
│ ┌───────────────┐ │
│ │     SES       │ │
│ │ Email Alerts  │ │
│ └───────────────┘ │
└───────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Monitoring & Operations                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │  CloudWatch  │  │   X-Ray      │  │   ECR       │  │
│  │  Logs/Metrics│  │   Tracing    │  │   Registry  │  │
│  └──────────────┘  └──────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Content Delivery & Edge

#### Amazon CloudFront
- **Purpose**: Global CDN for low-latency access across India
- **Features**:
  - Edge caching for static assets
  - SSL/TLS certificate management
  - DDoS protection via AWS Shield Standard
  - Origin failover for high availability
- **Configuration**:
  - Origin: API Gateway + S3 (static assets)
  - Cache behaviors: API (no-cache), Images (1-day TTL)
  - Geographic restrictions: None (India-focused)

### 2. API Management

#### Amazon API Gateway
- **Type**: REST API
- **Purpose**: Centralized API management and routing
- **Features**:
  - Request/response transformation
  - Rate limiting (10,000 req/sec burst)
  - API key management for partners
  - CORS configuration for web clients
  - Request validation
- **Endpoints**: `/api/v1/*`
- **Integration**: HTTP proxy to ALB

### 3. Authentication & Authorization

#### Amazon Cognito
- **User Pool**: Phone-based authentication
- **Features**:
  - SMS OTP verification (India +91)
  - JWT token generation
  - User attributes: phone, name, location, language_preference
  - MFA optional
- **Integration**: API Gateway authorizer
- **User Types**: Farmers, Buyers, Admins

### 4. Compute Layer

#### Amazon ECS Fargate
- **Service**: swadesh-ai-backend
- **Task Definition**:
  - Container: FastAPI application
  - CPU: 1 vCPU
  - Memory: 2 GB
  - Port: 8000
- **Auto Scaling**:
  - Min: 2 tasks
  - Max: 10 tasks
  - Target CPU: 70%
  - Target Memory: 80%
- **Health Checks**: `/api/v1/health`
- **Deployment**: Rolling update

#### Application Load Balancer (ALB)
- **Type**: Application Load Balancer
- **Listeners**: 
  - HTTP:80 → HTTPS:443 redirect
  - HTTPS:443 → Target Group (ECS tasks)
- **Health Check**: `/api/v1/health` (30s interval)
- **Stickiness**: Enabled (1 hour)

### 5. AI/ML Services

#### Amazon Bedrock
- **Model**: Claude 3 (Anthropic) or Nova Lite
- **Purpose**: Multilingual chatbot (Hindi + English)
- **Features**:
  - Context-aware agricultural advice
  - Conversational memory
  - Prompt engineering for farmer queries
- **API**: Bedrock Runtime API
- **Fallback**: Rule-based responses

#### Amazon Rekognition
- **Purpose**: Produce quality assessment from images
- **Features**:
  - Label detection (freshness indicators)
  - Custom labels (crop-specific)
  - Confidence scoring
- **Input**: S3 image URLs
- **Output**: Quality grade (A/B/C/D), freshness score

#### Amazon SageMaker (Optional)
- **Purpose**: Custom ML model hosting
- **Models**:
  - Spoilage prediction (XGBoost)
  - Price forecasting (LSTM)
- **Endpoints**: Real-time inference
- **Fallback**: In-container models (scikit-learn)

#### AWS Lambda
- **Functions**:
  - `spoilage-predictor`: Serverless ML inference
  - `price-forecaster`: Market trend analysis
  - `alert-processor`: Batch alert generation
- **Triggers**: EventBridge schedules, S3 events
- **Runtime**: Python 3.11

### 6. Data Storage

#### Amazon RDS PostgreSQL
- **Instance**: db.t3.medium (2 vCPU, 4 GB RAM)
- **Engine**: PostgreSQL 15
- **Storage**: 100 GB GP3 SSD
- **Multi-AZ**: Enabled (production)
- **Backup**: Automated daily snapshots (7-day retention)
- **Tables**:
  - `users` - Farmer/buyer profiles
  - `produce_batches` - Crop inventory
  - `transactions` - Sales records
  - `crop_types` - 16 supported crops
  - `buyers` - Verified buyer network
  - `auth_sessions` - Session management

#### Amazon DynamoDB
- **Tables**:
  - `swadesh-sessions` - User sessions (TTL: 24h)
  - `swadesh-alerts` - Real-time alerts
  - `swadesh-chat-history` - Chatbot conversations
  - `swadesh-market-prices` - Cached mandi prices
- **Capacity**: On-demand billing
- **Features**: Point-in-time recovery, encryption at rest

#### Amazon S3
- **Buckets**:
  - `swadesh-ai-images-{env}` - Crop images
  - `swadesh-ai-models-{env}` - ML model artifacts
  - `swadesh-ai-logs-{env}` - Application logs
- **Lifecycle Policies**:
  - Images: 90-day retention → Glacier
  - Logs: 30-day retention → deletion
- **Security**: Server-side encryption (SSE-S3)

#### Amazon Neptune (Optional)
- **Purpose**: Knowledge graph for causal reasoning
- **Instance**: db.t3.medium
- **Use Cases**:
  - Crop → shelf life relationships
  - Temperature → spoilage causality
  - Quality → price correlations

### 7. Notification Services

#### Amazon SNS
- **Topics**:
  - `swadesh-spoilage-alerts` - High-risk notifications
  - `swadesh-price-alerts` - Market opportunity alerts
  - `swadesh-buyer-matches` - New buyer notifications
- **Subscriptions**: SMS (Indian phone numbers)
- **Cost**: Pay-per-message

#### Amazon SES
- **Purpose**: Email notifications for buyers/admins
- **Features**:
  - Transactional emails
  - Bulk notifications
  - Bounce handling
- **Verified Domains**: swadesh-ai.com

### 8. Monitoring & Operations

#### Amazon CloudWatch
- **Metrics**:
  - ECS task CPU/memory utilization
  - API Gateway request count/latency
  - RDS connections/IOPS
  - Lambda invocations/errors
- **Alarms**:
  - High CPU (>80%) → SNS notification
  - API errors (>5%) → SNS notification
  - RDS storage (<20%) → SNS notification
- **Logs**:
  - Application logs (7-day retention)
  - Access logs (30-day retention)

#### AWS X-Ray
- **Purpose**: Distributed tracing
- **Features**:
  - Request flow visualization
  - Performance bottleneck identification
  - Error analysis

#### Amazon ECR
- **Purpose**: Docker image registry
- **Repositories**:
  - `swadesh-ai/backend` - FastAPI container
  - `swadesh-ai/ml-inference` - ML model container
- **Scanning**: Automated vulnerability scanning

### 9. Security

#### AWS IAM
- **Roles**:
  - `ECSTaskRole` - Backend service permissions
  - `LambdaExecutionRole` - Lambda function permissions
  - `CognitoRole` - User authentication
- **Policies**: Least privilege access

#### AWS Secrets Manager
- **Secrets**:
  - RDS database credentials
  - API keys (OpenWeatherMap, Mandi API)
  - Bedrock model access keys
- **Rotation**: Automatic (30 days)

#### AWS WAF (Optional)
- **Purpose**: Web application firewall
- **Rules**:
  - Rate limiting (100 req/5min per IP)
  - SQL injection protection
  - XSS protection

### 10. CI/CD Pipeline

#### AWS CodePipeline (Optional)
- **Stages**:
  1. Source: GitHub repository
  2. Build: CodeBuild (Docker image)
  3. Deploy: ECS Fargate rolling update
- **Triggers**: Git push to main branch

## Network Architecture

### VPC Configuration
- **CIDR**: 10.0.0.0/16
- **Subnets**:
  - Public Subnet 1: 10.0.1.0/24 (AZ-a)
  - Public Subnet 2: 10.0.2.0/24 (AZ-b)
  - Private Subnet 1: 10.0.3.0/24 (AZ-a)
  - Private Subnet 2: 10.0.4.0/24 (AZ-b)
- **Internet Gateway**: Public subnet internet access
- **NAT Gateway**: Private subnet outbound access
- **Security Groups**:
  - ALB-SG: Allow 80, 443 from 0.0.0.0/0
  - ECS-SG: Allow 8000 from ALB-SG
  - RDS-SG: Allow 5432 from ECS-SG
  - Neptune-SG: Allow 8182 from ECS-SG

## Data Flow

### 1. Crop Quality Assessment Flow
```
Farmer → Android App → CloudFront → API Gateway → Cognito Auth
  → ALB → ECS (FastAPI) → S3 (upload image)
  → Rekognition (analyze) → RDS (store results)
  → Response → Farmer
```

### 2. Spoilage Prediction Flow
```
Farmer → Request spoilage assessment → API Gateway → ECS
  → Weather Service (OpenWeatherMap API)
  → Spoilage Service (Q10 model calculation)
  → RDS (store prediction) → DynamoDB (cache)
  → Response with risk level → Farmer
```

### 3. Price Intelligence Flow
```
Scheduled Lambda → Fetch mandi prices (data.gov.in)
  → DynamoDB (cache prices) → Price Service
  → Calculate trends → RDS (store)
  → SNS (alert if opportunity) → Farmer SMS
```

### 4. Buyer Matching Flow
```
Farmer → Request buyers → API Gateway → ECS
  → Buyer Service → RDS (query buyers)
  → Location Service (calculate distance)
  → Sort by proximity + price → Response
```

### 5. Chatbot Flow
```
Farmer → Chat message → API Gateway → ECS
  → Chatbot Service → DynamoDB (fetch history)
  → Bedrock (Claude) → Generate response
  → DynamoDB (store message) → Response
```

## Deployment Architecture

### Development Environment
- **ECS Tasks**: 1
- **RDS**: db.t3.micro (single-AZ)
- **DynamoDB**: On-demand
- **Cost**: ~$50-100/month

### Production Environment
- **ECS Tasks**: 2-10 (auto-scaling)
- **RDS**: db.t3.medium (Multi-AZ)
- **DynamoDB**: Provisioned capacity
- **CloudFront**: Enabled
- **WAF**: Enabled
- **Cost**: ~$300-500/month

## Scalability

### Horizontal Scaling
- **ECS Fargate**: Auto-scales based on CPU/memory
- **API Gateway**: Handles 10,000 req/sec
- **DynamoDB**: Auto-scales read/write capacity
- **S3**: Unlimited storage

### Vertical Scaling
- **RDS**: Can upgrade to larger instances
- **ECS Tasks**: Can increase CPU/memory allocation

### Geographic Scaling
- **CloudFront**: 450+ edge locations globally
- **Multi-region**: Can deploy to multiple AWS regions

## Cost Optimization

1. **ECS Fargate Spot**: 70% cost savings for non-critical tasks
2. **S3 Intelligent-Tiering**: Automatic cost optimization
3. **DynamoDB On-Demand**: Pay only for actual usage
4. **Reserved Instances**: RDS reserved for 1-year (40% savings)
5. **Lambda**: Serverless pricing (pay per invocation)

## Disaster Recovery

### Backup Strategy
- **RDS**: Automated daily snapshots (7-day retention)
- **DynamoDB**: Point-in-time recovery (35-day window)
- **S3**: Versioning enabled, cross-region replication

### Recovery Time Objective (RTO)
- **Target**: < 1 hour
- **Strategy**: Multi-AZ deployment, automated failover

### Recovery Point Objective (RPO)
- **Target**: < 5 minutes
- **Strategy**: Continuous replication, transaction logs

## Security Architecture

### Data Encryption
- **At Rest**: 
  - RDS: AES-256 encryption
  - DynamoDB: AWS-managed keys
  - S3: SSE-S3 encryption
- **In Transit**: TLS 1.2+ for all connections

### Network Security
- **VPC Isolation**: Private subnets for data layer
- **Security Groups**: Least privilege access
- **NACLs**: Additional network layer protection

### Compliance
- **Data Residency**: All data stored in AWS India (Mumbai) region
- **Audit Logging**: CloudTrail enabled for all API calls
- **Access Control**: IAM roles with MFA for admins

## Performance Benchmarks

| Metric | Target | Actual |
|--------|--------|--------|
| API Response Time | < 500ms | 200-400ms |
| Image Upload | < 5s | 2-3s |
| Spoilage Prediction | < 2s | 1-1.5s |
| Chatbot Response | < 3s | 2-4s |
| Dashboard Load | < 3s | 1-2s |
| Concurrent Users | 10,000+ | Tested 5,000 |

## AWS Service Costs (Monthly Estimate)

| Service | Development | Production |
|---------|-------------|------------|
| ECS Fargate | $30 | $150 |
| RDS PostgreSQL | $15 | $100 |
| DynamoDB | $5 | $30 |
| S3 | $5 | $20 |
| API Gateway | $10 | $50 |
| Bedrock (Claude) | $20 | $100 |
| Rekognition | $10 | $40 |
| CloudFront | $5 | $30 |
| SNS/SES | $5 | $20 |
| CloudWatch | $5 | $15 |
| **Total** | **~$110** | **~$555** |

## Deployment Regions

### Primary Region
- **ap-south-1** (Mumbai, India)
- Lowest latency for Indian farmers
- All services available

### Backup Region (Optional)
- **ap-southeast-1** (Singapore)
- Disaster recovery failover

## Infrastructure as Code

The entire infrastructure is defined in:
- **CloudFormation**: `infra/cloudformation/main-stack.yaml`
- **Terraform**: `infra/terraform/` (alternative)
- **Docker**: `backend/Dockerfile.aws`

## Deployment Commands

```bash
# Deploy CloudFormation stack
cd infra
./deploy.sh dev YourDBPassword123

# Build and push Docker image
cd backend
docker build -f Dockerfile.aws -t swadesh-ai:latest .
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-south-1.amazonaws.com
docker tag swadesh-ai:latest <account-id>.dkr.ecr.ap-south-1.amazonaws.com/swadesh-ai:latest
docker push <account-id>.dkr.ecr.ap-south-1.amazonaws.com/swadesh-ai:latest

# Update ECS service
aws ecs update-service --cluster swadesh-ai-cluster --service swadesh-ai-backend --force-new-deployment
```

## Architecture Decisions

### Why ECS Fargate over Lambda?
- FastAPI requires persistent connections
- Complex ML inference (>15s timeout)
- WebSocket support for real-time updates

### Why RDS + DynamoDB hybrid?
- RDS: Relational data (users, transactions)
- DynamoDB: High-velocity data (sessions, alerts, chat)

### Why Bedrock over self-hosted LLM?
- Managed service (no infrastructure)
- Multi-language support
- Cost-effective for hackathon scale

### Why CloudFront?
- India has variable network quality
- Edge caching reduces latency
- DDoS protection included

## Future Enhancements

1. **Multi-region deployment** for disaster recovery
2. **Neptune knowledge graph** for advanced causal reasoning
3. **SageMaker Pipelines** for automated model retraining
4. **AppSync GraphQL** for real-time subscriptions
5. **Amplify** for web app hosting
6. **QuickSight** for analytics dashboards

---

**Last Updated**: March 2026  
**Version**: 1.0  
**Team**: SwadeshAI
