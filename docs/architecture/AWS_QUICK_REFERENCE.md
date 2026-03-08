# SwadeshAI - AWS Quick Reference Guide

## Essential AWS Resources

### API Endpoints
```
CloudFront:     https://<distribution-id>.cloudfront.net
API Gateway:    https://<api-id>.execute-api.ap-south-1.amazonaws.com/v1
ALB:            http://<alb-dns>.ap-south-1.elb.amazonaws.com
Health Check:   /api/v1/health
```

### Database Connections
```
RDS Endpoint:   swadesh-ai-db.<id>.ap-south-1.rds.amazonaws.com:5432
Database:       swadesh_ai
Username:       swadesh_admin
Password:       (stored in Secrets Manager)

Connection String:
postgresql://swadesh_admin:<password>@<rds-endpoint>:5432/swadesh_ai
```

### S3 Buckets
```
Images:   swadesh-ai-images-{env}
Models:   swadesh-ai-models-{env}
Logs:     swadesh-ai-logs-{env}
```

### DynamoDB Tables
```
swadesh-sessions        (session_id: String)
swadesh-alerts          (user_id: String, timestamp: Number)
swadesh-chat-history    (user_id: String, message_id: String)
swadesh-market-prices   (crop_type: String, date: String)
```

## Common AWS CLI Commands

### ECS Operations
```bash
# List running tasks
aws ecs list-tasks --cluster swadesh-ai-cluster

# Describe service
aws ecs describe-services --cluster swadesh-ai-cluster --services swadesh-ai-backend

# Update service (force new deployment)
aws ecs update-service --cluster swadesh-ai-cluster --service swadesh-ai-backend --force-new-deployment

# View task logs
aws logs tail /ecs/swadesh-ai --follow

# Scale service
aws ecs update-service --cluster swadesh-ai-cluster --service swadesh-ai-backend --desired-count 5
```

### RDS Operations
```bash
# Describe database
aws rds describe-db-instances --db-instance-identifier swadesh-ai-db

# Create snapshot
aws rds create-db-snapshot --db-instance-identifier swadesh-ai-db --db-snapshot-identifier backup-$(date +%Y%m%d)

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot --db-instance-identifier swadesh-ai-db-restored --db-snapshot-identifier backup-20260308

# Modify instance class
aws rds modify-db-instance --db-instance-identifier swadesh-ai-db --db-instance-class db.t3.large --apply-immediately
```

### S3 Operations
```bash
# List buckets
aws s3 ls

# Upload file
aws s3 cp local-file.jpg s3://swadesh-ai-images-dev/crops/

# Download file
aws s3 cp s3://swadesh-ai-images-dev/crops/image.jpg ./

# Sync directory
aws s3 sync ./ml/models/ s3://swadesh-ai-models-dev/models/

# Delete old files
aws s3 rm s3://swadesh-ai-images-dev/crops/ --recursive --exclude "*" --include "2025-*"
```

### DynamoDB Operations
```bash
# Scan table
aws dynamodb scan --table-name swadesh-sessions --max-items 10

# Get item
aws dynamodb get-item --table-name swadesh-sessions --key '{"session_id": {"S": "abc123"}}'

# Put item
aws dynamodb put-item --table-name swadesh-alerts --item '{"user_id": {"S": "user123"}, "timestamp": {"N": "1234567890"}}'

# Enable point-in-time recovery
aws dynamodb update-continuous-backups --table-name swadesh-sessions --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

### CloudWatch Operations
```bash
# View logs
aws logs tail /ecs/swadesh-ai --follow

# Create alarm
aws cloudwatch put-metric-alarm --alarm-name high-cpu --metric-name CPUUtilization --namespace AWS/ECS --statistic Average --period 300 --threshold 80 --comparison-operator GreaterThanThreshold

# List alarms
aws cloudwatch describe-alarms

# Get metrics
aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization --start-time 2026-03-08T00:00:00Z --end-time 2026-03-08T23:59:59Z --period 3600 --statistics Average
```

### Secrets Manager Operations
```bash
# Get secret value
aws secretsmanager get-secret-value --secret-id /swadesh-ai/db-password

# Update secret
aws secretsmanager update-secret --secret-id /swadesh-ai/db-password --secret-string "NewPassword123"

# Create secret
aws secretsmanager create-secret --name /swadesh-ai/api-keys --secret-string '{"key": "value"}'
```

## Environment Variables Reference

### Required for ECS Task
```bash
# Database
DB_HOST=<rds-endpoint>
DB_NAME=swadesh_ai
DB_USER=swadesh_admin
DB_PASSWORD=<from-secrets-manager>
DB_PORT=5432

# AWS Configuration
AWS_REGION=ap-south-1
AWS_DEFAULT_REGION=ap-south-1

# S3
S3_BUCKET=swadesh-ai-images-dev

# DynamoDB
DYNAMODB_SESSIONS_TABLE=swadesh-sessions
DYNAMODB_ALERTS_TABLE=swadesh-alerts
DYNAMODB_CHAT_TABLE=swadesh-chat-history
DYNAMODB_PRICES_TABLE=swadesh-market-prices

# AI Services
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
REKOGNITION_MIN_CONFIDENCE=70

# External APIs
OPENWEATHER_API_KEY=<from-secrets-manager>
MANDI_API_KEY=<from-secrets-manager>

# Application
ENVIRONMENT=dev
LOG_LEVEL=INFO
```

## IAM Permissions Reference

### ECS Task Role Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::swadesh-ai-images-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "rekognition:DetectLabels",
        "rekognition:DetectModerationLabels"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:ap-south-1:*:table/swadesh-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:ap-south-1:*:swadesh-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:ap-south-1:*:secret:/swadesh-ai/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:ap-south-1:*:log-group:/ecs/swadesh-ai:*"
    }
  ]
}
```

## Monitoring Queries

### CloudWatch Insights Queries

#### Find API Errors
```sql
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

#### Slow Requests
```sql
fields @timestamp, request_duration, endpoint
| filter request_duration > 1000
| sort request_duration desc
| limit 50
```

#### Spoilage Predictions
```sql
fields @timestamp, batch_id, risk_level, shelf_life_days
| filter @message like /spoilage_prediction/
| stats count() by risk_level
```

#### Chatbot Usage
```sql
fields @timestamp, user_id, language
| filter @message like /chatbot_request/
| stats count() by language
```

## Troubleshooting Guide

### Issue: ECS Tasks Not Starting
```bash
# Check task status
aws ecs describe-tasks --cluster swadesh-ai-cluster --tasks <task-id>

# Check logs
aws logs tail /ecs/swadesh-ai --follow

# Common causes:
# - Image pull error (check ECR permissions)
# - Health check failing (check /api/v1/health endpoint)
# - Resource limits (check CPU/memory)
```

### Issue: Database Connection Timeout
```bash
# Test connectivity
aws ec2 describe-security-groups --group-ids <rds-sg-id>

# Check RDS status
aws rds describe-db-instances --db-instance-identifier swadesh-ai-db

# Common causes:
# - Security group not allowing ECS-SG
# - RDS in wrong subnet
# - Connection string incorrect
```

### Issue: Rekognition Access Denied
```bash
# Check IAM role permissions
aws iam get-role-policy --role-name ECSTaskRole --policy-name RekognitionAccess

# Test Rekognition access
aws rekognition detect-labels --image '{"S3Object":{"Bucket":"swadesh-ai-images-dev","Name":"test.jpg"}}'

# Common causes:
# - IAM role missing rekognition:DetectLabels
# - S3 bucket policy blocking Rekognition
```

### Issue: Bedrock Model Not Found
```bash
# List available models
aws bedrock list-foundation-models --region ap-south-1

# Check model access
aws bedrock get-foundation-model --model-identifier amazon.nova-lite-v1:0

# Common causes:
# - Model not available in region
# - Model ID incorrect
# - Bedrock access not enabled
```

## Performance Tuning

### ECS Task Optimization
```bash
# Increase task count for high load
aws ecs update-service --cluster swadesh-ai-cluster --service swadesh-ai-backend --desired-count 5

# Increase task resources
# Update task definition with:
# - CPU: 2048 (2 vCPU)
# - Memory: 4096 (4 GB)
```

### RDS Optimization
```bash
# Enable Performance Insights
aws rds modify-db-instance --db-instance-identifier swadesh-ai-db --enable-performance-insights

# Add read replica
aws rds create-db-instance-read-replica --db-instance-identifier swadesh-ai-db-replica --source-db-instance-identifier swadesh-ai-db
```

### DynamoDB Optimization
```bash
# Switch to provisioned capacity for predictable load
aws dynamodb update-table --table-name swadesh-sessions --billing-mode PROVISIONED --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=5

# Enable auto-scaling
aws application-autoscaling register-scalable-target --service-namespace dynamodb --resource-id table/swadesh-sessions --scalable-dimension dynamodb:table:ReadCapacityUnits --min-capacity 5 --max-capacity 100
```

## Cost Optimization Tips

1. **Use Fargate Spot** for dev environments (70% savings)
2. **Enable S3 Intelligent-Tiering** for automatic cost optimization
3. **Use DynamoDB on-demand** for variable workloads
4. **Purchase RDS Reserved Instances** for production (40% savings)
5. **Enable CloudWatch Logs retention** (7 days for dev, 30 days for prod)
6. **Use Lambda for batch jobs** instead of always-on containers
7. **Enable CloudFront caching** for static assets
8. **Delete old ECS task definitions** to reduce clutter

## Security Checklist

- [ ] Enable MFA for AWS root account
- [ ] Enable CloudTrail for audit logging
- [ ] Enable GuardDuty for threat detection
- [ ] Rotate database passwords monthly
- [ ] Enable RDS encryption at rest
- [ ] Enable S3 bucket versioning
- [ ] Configure WAF rules for API Gateway
- [ ] Enable VPC Flow Logs
- [ ] Review IAM policies (least privilege)
- [ ] Enable automated backups (RDS, DynamoDB)
- [ ] Configure CloudWatch alarms
- [ ] Enable X-Ray tracing
- [ ] Review security group rules
- [ ] Enable ECR image scanning

## Useful AWS Console Links

```
ECS Console:
https://ap-south-1.console.aws.amazon.com/ecs/v2/clusters/swadesh-ai-cluster

RDS Console:
https://ap-south-1.console.aws.amazon.com/rds/home?region=ap-south-1#database:id=swadesh-ai-db

CloudWatch Logs:
https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#logsV2:log-groups/log-group/$252Fecs$252Fswadesh-ai

API Gateway:
https://ap-south-1.console.aws.amazon.com/apigateway/main/apis

CloudFront:
https://console.aws.amazon.com/cloudfront/v3/home

Cognito:
https://ap-south-1.console.aws.amazon.com/cognito/v2/idp/user-pools
```

## Emergency Contacts & Runbooks

### High CPU Alert
1. Check CloudWatch metrics
2. Review slow queries in RDS
3. Scale ECS tasks: `aws ecs update-service --desired-count 5`
4. Investigate logs for bottlenecks

### Database Connection Pool Exhausted
1. Check active connections: `SELECT count(*) FROM pg_stat_activity;`
2. Increase max_connections in RDS parameter group
3. Optimize connection pooling in FastAPI
4. Consider read replicas

### S3 Storage Full
1. Check bucket size: `aws s3 ls s3://swadesh-ai-images-dev --recursive --summarize`
2. Enable lifecycle policies
3. Archive old images to Glacier
4. Increase storage quota if needed

### Bedrock Rate Limit Exceeded
1. Implement exponential backoff
2. Cache common responses
3. Request quota increase
4. Use fallback rule-based responses

---

**Last Updated**: March 2026  
**Version**: 1.0  
**Team**: SwadeshAI
