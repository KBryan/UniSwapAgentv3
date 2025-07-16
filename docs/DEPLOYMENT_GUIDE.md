# NFT-Gated AI Trading Bot Deployment Guide

This comprehensive guide covers all aspects of deploying the NFT-Gated AI Trading Bot across different environments, from local development to production-scale deployments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Local Development Deployment](#local-development-deployment)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Heroku Deployment](#heroku-deployment)
- [AWS Deployment](#aws-deployment)
- [Monitoring and Observability](#monitoring-and-observability)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Maintenance and Updates](#maintenance-and-updates)

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **Network**: Stable internet connection with low latency

#### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **Network**: High-speed internet with redundant connections

### Software Dependencies

#### Required Software
- **Python**: 3.11 or higher
- **Docker**: 20.10 or higher
- **Docker Compose**: 2.0 or higher
- **PostgreSQL**: 15 or higher
- **Redis**: 7 or higher

#### Optional Software
- **Kubernetes**: 1.25 or higher (for K8s deployment)
- **Helm**: 3.0 or higher (for K8s package management)
- **Node.js**: 18 or higher (for frontend development)

### External Services

#### Required Services
- **Blockchain RPC Providers**: Alchemy, Infura, or similar
- **Database**: PostgreSQL (managed or self-hosted)
- **Cache/Message Broker**: Redis (managed or self-hosted)

#### Optional Services
- **LLM Providers**: Anthropic, OpenAI, Google Gemini, Venice AI
- **Market Data**: CoinGecko API
- **Social Media**: Twitter API
- **Monitoring**: Prometheus, Grafana, DataDog, or similar

## Environment Configuration

### Environment Variables

The application uses environment variables for configuration. Create environment-specific files:

#### Development Environment (`.env.development`)

```bash
# Application Settings
DEBUG=true
BYPASS_NFT_GATE=true
REAL_DATA_MODE=false
SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/nft_trading_bot_dev

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Blockchain Configuration
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/your-dev-api-key
PRIVATE_KEY=0x0000000000000000000000000000000000000000000000000000000000000000

# API Keys (Development)
ANTHROPIC_API_KEY=your-dev-anthropic-api-key
OPENAI_API_KEY=your-dev-openai-api-key
COINGECKO_API_KEY=your-dev-coingecko-api-key

# Trading Configuration
MAX_GAS_PRICE=100
DEFAULT_SLIPPAGE=0.5
MIN_TRADE_AMOUNT=0.001
```

#### Production Environment (`.env.production`)

```bash
# Application Settings
DEBUG=false
BYPASS_NFT_GATE=false
REAL_DATA_MODE=true
SECRET_KEY=your-super-secret-production-key-min-32-chars

# Database Configuration
DATABASE_URL=postgresql://username:password@your-db-host:5432/nft_trading_bot_prod

# Redis Configuration
REDIS_URL=redis://your-redis-host:6379/0

# Blockchain Configuration
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/your-production-api-key
PRIVATE_KEY=your-production-private-key-with-sufficient-funds

# API Keys (Production)
ANTHROPIC_API_KEY=your-production-anthropic-api-key
OPENAI_API_KEY=your-production-openai-api-key
COINGECKO_API_KEY=your-production-coingecko-api-key

# Trading Configuration
MAX_GAS_PRICE=50
DEFAULT_SLIPPAGE=0.3
MIN_TRADE_AMOUNT=0.01

# Security
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
CORS_ORIGINS=https://your-frontend.com,https://app.your-domain.com
```

### Configuration Management

#### Using Environment Files

1. **Copy template files**:
   ```bash
   cp .env.example .env.development
   cp .env.production.template .env.production
   ```

2. **Edit configuration**:
   ```bash
   nano .env.development
   nano .env.production
   ```

3. **Validate configuration**:
   ```bash
   python -c "from config import get_settings; print(get_settings())"
   ```

#### Using External Configuration Management

For production deployments, consider using external configuration management:

- **Kubernetes Secrets**: Store sensitive data in K8s secrets
- **AWS Parameter Store**: Use AWS Systems Manager Parameter Store
- **HashiCorp Vault**: Enterprise-grade secret management
- **Azure Key Vault**: Microsoft Azure secret management

## Local Development Deployment

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/nft-trading-bot.git
   cd nft-trading-bot
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env.development
   # Edit .env.development with your settings
   ```

4. **Start services**:
   ```bash
   docker-compose up -d postgres redis
   ```

5. **Run database migrations**:
   ```bash
   python -m alembic upgrade head
   ```

6. **Start the application**:
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Start Celery worker** (in another terminal):
   ```bash
   celery -A core.celery_app worker --loglevel=info
   ```

8. **Start Celery beat** (in another terminal):
   ```bash
   celery -A core.celery_app beat --loglevel=info
   ```

### Development with Docker Compose

For a complete development environment using Docker:

```bash
# Start all services
docker-compose up --build

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Reset database
docker-compose down -v
docker-compose up --build
```

### Development Tools

#### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Monitoring
- **Flower (Celery)**: http://localhost:5555
- **Redis Commander**: http://localhost:8081

#### Database Management
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d nft_trading_bot_dev

# View database logs
docker-compose logs postgres
```

## Docker Deployment

### Building Docker Images

#### Build Production Image

```bash
# Build the image
docker build -t nft-trading-bot:latest .

# Tag for registry
docker tag nft-trading-bot:latest your-registry/nft-trading-bot:v1.0.0

# Push to registry
docker push your-registry/nft-trading-bot:v1.0.0
```

#### Multi-stage Build for Optimization

The Dockerfile uses multi-stage builds for optimization:

```dockerfile
# Development stage
FROM python:3.11-slim as development
# ... development dependencies

# Production stage
FROM python:3.11-slim as production
# ... production optimizations
```

### Docker Compose Production Deployment

#### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    image: your-registry/nft-trading-bot:latest
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - REAL_DATA_MODE=true
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  worker:
    image: your-registry/nft-trading-bot:latest
    command: celery -A core.celery_app worker --loglevel=info
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  scheduler:
    image: your-registry/nft-trading-bot:latest
    command: celery -A core.celery_app beat --loglevel=info
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: nft_trading_bot_prod
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### Deploy with Docker Compose

```bash
# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=3

# Update deployment
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Docker Swarm Deployment

For multi-node deployments using Docker Swarm:

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml nft-trading-bot

# View services
docker service ls

# Scale services
docker service scale nft-trading-bot_worker=3

# Update service
docker service update --image your-registry/nft-trading-bot:v1.1.0 nft-trading-bot_api
```

## Kubernetes Deployment

### Prerequisites

1. **Kubernetes cluster** (1.25+)
2. **kubectl** configured
3. **Helm** (optional, for package management)
4. **Ingress controller** (nginx, traefik, etc.)
5. **Cert-manager** (for SSL certificates)

### Namespace Setup

```bash
# Create namespace
kubectl create namespace nft-trading-bot

# Set default namespace
kubectl config set-context --current --namespace=nft-trading-bot
```

### Secrets Management

```bash
# Create secrets from environment file
kubectl create secret generic nft-trading-bot-secrets \
  --from-env-file=.env.production

# Or create individual secrets
kubectl create secret generic database-secret \
  --from-literal=url="postgresql://username:password@host:5432/db"

kubectl create secret generic api-keys \
  --from-literal=anthropic-key="your-key" \
  --from-literal=openai-key="your-key"
```

### ConfigMaps

```bash
# Create configmap for non-sensitive configuration
kubectl create configmap nft-trading-bot-config \
  --from-literal=debug="false" \
  --from-literal=real-data-mode="true" \
  --from-literal=max-gas-price="50"
```

### Deployment

#### Apply Kubernetes Manifests

```bash
# Apply all manifests
kubectl apply -f k8s/

# Or apply individually
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

#### Verify Deployment

```bash
# Check deployments
kubectl get deployments

# Check pods
kubectl get pods

# Check services
kubectl get services

# Check ingress
kubectl get ingress

# View logs
kubectl logs deployment/nft-trading-bot-api
```

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nft-trading-bot-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nft-trading-bot-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Persistent Volumes

For stateful components:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: fast-ssd
```

### Helm Chart Deployment

Create a Helm chart for easier management:

```bash
# Create Helm chart
helm create nft-trading-bot-chart

# Install chart
helm install nft-trading-bot ./nft-trading-bot-chart

# Upgrade chart
helm upgrade nft-trading-bot ./nft-trading-bot-chart

# Rollback
helm rollback nft-trading-bot 1
```

## Heroku Deployment

### Prerequisites

1. **Heroku CLI** installed
2. **Heroku account** with billing enabled
3. **Git** repository

### Initial Setup

```bash
# Login to Heroku
heroku login

# Create Heroku app
heroku create your-nft-trading-bot

# Add buildpacks
heroku buildpacks:add heroku/python

# Set stack
heroku stack:set heroku-22
```

### Add-ons

```bash
# PostgreSQL database
heroku addons:create heroku-postgresql:standard-0

# Redis cache
heroku addons:create heroku-redis:premium-0

# Papertrail logging
heroku addons:create papertrail:choklad

# New Relic monitoring
heroku addons:create newrelic:wayne
```

### Configuration

```bash
# Set environment variables
heroku config:set DEBUG=false
heroku config:set BYPASS_NFT_GATE=false
heroku config:set REAL_DATA_MODE=true
heroku config:set SECRET_KEY=your-production-secret-key

# Set API keys
heroku config:set ANTHROPIC_API_KEY=your-key
heroku config:set OPENAI_API_KEY=your-key
heroku config:set COINGECKO_API_KEY=your-key

# Set blockchain configuration
heroku config:set ETHEREUM_RPC_URL=your-rpc-url
heroku config:set PRIVATE_KEY=your-private-key

# Set trading parameters
heroku config:set MAX_GAS_PRICE=50
heroku config:set DEFAULT_SLIPPAGE=0.3
```

### Deployment

```bash
# Deploy to Heroku
git push heroku main

# Run database migrations
heroku run python -m alembic upgrade head

# Scale dynos
heroku ps:scale web=2 worker=2

# View logs
heroku logs --tail

# Open application
heroku open
```

### Process Types

The `Procfile` defines process types:

```
web: gunicorn api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
worker: celery -A core.celery_app worker --loglevel=info --concurrency=2
beat: celery -A core.celery_app beat --loglevel=info
```

### Heroku Scheduler

For periodic tasks:

```bash
# Add scheduler add-on
heroku addons:create scheduler:standard

# Open scheduler dashboard
heroku addons:open scheduler
```

## AWS Deployment

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │    │   Application   │    │   ECS Cluster   │
│   (CDN/WAF)     │────│  Load Balancer  │────│   (Fargate)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Route 53      │    │   API Gateway   │    │   Lambda        │
│   (DNS)         │    │   (API Mgmt)    │    │   (Functions)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RDS           │    │   ElastiCache   │    │   S3            │
│   (PostgreSQL)  │    │   (Redis)       │    │   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### ECS Deployment

#### Task Definition

```json
{
  "family": "nft-trading-bot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/nft-trading-bot:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DEBUG",
          "value": "false"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:ssm:region:account:parameter/nft-trading-bot/database-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/nft-trading-bot",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Service Definition

```json
{
  "serviceName": "nft-trading-bot-api",
  "cluster": "nft-trading-bot-cluster",
  "taskDefinition": "nft-trading-bot:1",
  "desiredCount": 2,
  "launchType": "FARGATE",
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": ["subnet-12345", "subnet-67890"],
      "securityGroups": ["sg-12345"],
      "assignPublicIp": "ENABLED"
    }
  },
  "loadBalancers": [
    {
      "targetGroupArn": "arn:aws:elasticloadbalancing:region:account:targetgroup/nft-trading-bot/1234567890123456",
      "containerName": "api",
      "containerPort": 8000
    }
  ]
}
```

### RDS Setup

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier nft-trading-bot-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.4 \
  --allocated-storage 100 \
  --storage-type gp2 \
  --db-name nft_trading_bot_prod \
  --master-username postgres \
  --master-user-password your-secure-password \
  --vpc-security-group-ids sg-12345 \
  --db-subnet-group-name default \
  --backup-retention-period 7 \
  --multi-az \
  --storage-encrypted
```

### ElastiCache Setup

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id nft-trading-bot-redis \
  --cache-node-type cache.t3.medium \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --cache-subnet-group-name default \
  --security-group-ids sg-12345
```

### Parameter Store Configuration

```bash
# Store sensitive configuration in Parameter Store
aws ssm put-parameter \
  --name "/nft-trading-bot/database-url" \
  --value "postgresql://username:password@host:5432/db" \
  --type "SecureString"

aws ssm put-parameter \
  --name "/nft-trading-bot/anthropic-api-key" \
  --value "your-api-key" \
  --type "SecureString"
```

### CloudFormation Template

Create infrastructure as code:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'NFT Trading Bot Infrastructure'

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues: [development, staging, production]

Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true

  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub '${Environment}-nft-trading-bot'

  RDSInstance:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: !Sub '${Environment}-nft-trading-bot-db'
      DBInstanceClass: db.t3.medium
      Engine: postgres
      EngineVersion: '15.4'
      AllocatedStorage: 100
      DBName: nft_trading_bot
      MasterUsername: postgres
      MasterUserPassword: !Ref DBPassword

Outputs:
  ClusterName:
    Description: ECS Cluster Name
    Value: !Ref ECSCluster
    Export:
      Name: !Sub '${Environment}-ECSCluster'
```

## Monitoring and Observability

### Prometheus and Grafana

#### Prometheus Configuration

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'nft-trading-bot'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

#### Grafana Dashboards

Create dashboards for:
- **Application Metrics**: Request rate, response time, error rate
- **Trading Metrics**: Trade volume, success rate, P&L
- **System Metrics**: CPU, memory, disk usage
- **Database Metrics**: Connection count, query performance
- **Celery Metrics**: Task queue length, worker status

### Application Metrics

The application exposes metrics at `/metrics`:

```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Trading metrics
TRADE_COUNT = Counter('trades_total', 'Total trades executed', ['status', 'token_pair'])
TRADE_VOLUME = Gauge('trade_volume_usd', 'Trading volume in USD')
```

### Logging

#### Structured Logging

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "Trade executed",
    trade_id="trade_123",
    token_in="ETH",
    token_out="USDC",
    amount_in=1.0,
    amount_out=1595.50,
    user_wallet="0x..."
)
```

#### Log Aggregation

Use centralized logging:
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Fluentd**: Log collection and forwarding
- **Loki**: Grafana's log aggregation system
- **CloudWatch**: AWS native logging

### Health Checks

The application provides multiple health check endpoints:

```bash
# Liveness probe
curl http://localhost:8000/health/live

# Readiness probe
curl http://localhost:8000/health/ready

# Comprehensive health check
curl http://localhost:8000/health/
```

### Alerting

#### Prometheus Alerting Rules

```yaml
groups:
  - name: nft-trading-bot
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected

      - alert: DatabaseConnectionFailure
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: Database connection failure

      - alert: HighTradeFailureRate
        expr: rate(trades_total{status="failed"}[10m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High trade failure rate
```

#### Notification Channels

Configure alerts to send notifications via:
- **Slack**: Webhook integration
- **Discord**: Webhook integration
- **Email**: SMTP configuration
- **PagerDuty**: Incident management
- **Telegram**: Bot notifications

## Security Considerations

### Network Security

#### Firewall Rules

```bash
# Allow HTTP/HTTPS traffic
ufw allow 80/tcp
ufw allow 443/tcp

# Allow SSH (restrict to specific IPs)
ufw allow from 192.168.1.0/24 to any port 22

# Allow database access (internal only)
ufw allow from 10.0.0.0/8 to any port 5432

# Deny all other traffic
ufw default deny incoming
ufw default allow outgoing
```

#### SSL/TLS Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
}
```

### Application Security

#### Environment Variables

Never commit sensitive data:

```bash
# Use .gitignore
echo ".env*" >> .gitignore
echo "*.key" >> .gitignore
echo "secrets/" >> .gitignore
```

#### Secret Management

Use proper secret management:

```bash
# Kubernetes secrets
kubectl create secret generic api-keys \
  --from-literal=anthropic="$(cat anthropic.key)" \
  --from-literal=openai="$(cat openai.key)"

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name "nft-trading-bot/api-keys" \
  --secret-string file://secrets.json
```

#### Input Validation

Implement comprehensive input validation:

```python
from pydantic import BaseModel, validator

class TradeRequest(BaseModel):
    token_in: str
    token_out: str
    amount: float
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
```

### Database Security

#### Connection Security

```python
# Use SSL connections
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require"

# Connection pooling with limits
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

#### Access Control

```sql
-- Create application user with limited privileges
CREATE USER nft_trading_bot WITH PASSWORD 'secure_password';

-- Grant only necessary permissions
GRANT CONNECT ON DATABASE nft_trading_bot_prod TO nft_trading_bot;
GRANT USAGE ON SCHEMA public TO nft_trading_bot;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nft_trading_bot;
```

### Monitoring Security

#### Audit Logging

```python
import logging

audit_logger = logging.getLogger('audit')

def log_trade_execution(user_wallet, trade_details):
    audit_logger.info(
        "Trade executed",
        extra={
            "user_wallet": user_wallet,
            "trade_id": trade_details.trade_id,
            "amount": trade_details.amount,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

#### Security Scanning

```bash
# Dependency vulnerability scanning
pip install safety
safety check

# Code security scanning
pip install bandit
bandit -r .

# Container scanning
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image nft-trading-bot:latest
```

## Troubleshooting

### Common Issues

#### Database Connection Issues

```bash
# Check database connectivity
pg_isready -h localhost -p 5432

# Test connection with psql
psql -h localhost -p 5432 -U postgres -d nft_trading_bot_dev

# Check connection pool status
curl http://localhost:8000/health/ | jq '.services.database'
```

#### Redis Connection Issues

```bash
# Check Redis connectivity
redis-cli ping

# Monitor Redis
redis-cli monitor

# Check memory usage
redis-cli info memory
```

#### Celery Issues

```bash
# Check Celery worker status
celery -A core.celery_app inspect active

# Check task queue
celery -A core.celery_app inspect reserved

# Purge failed tasks
celery -A core.celery_app purge
```

#### Blockchain Connection Issues

```bash
# Test RPC connectivity
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  $ETHEREUM_RPC_URL

# Check gas prices
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":1}' \
  $ETHEREUM_RPC_URL
```

### Performance Issues

#### Database Performance

```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE tablename = 'trades';
```

#### Application Performance

```bash
# Profile application
pip install py-spy
py-spy top --pid $(pgrep -f "uvicorn")

# Memory profiling
pip install memory-profiler
python -m memory_profiler api/main.py
```

#### Container Performance

```bash
# Check container resource usage
docker stats

# Check container logs for errors
docker logs nft-trading-bot-api

# Check disk usage
docker system df
```

### Debugging

#### Enable Debug Mode

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
uvicorn api.main:app --reload --log-level debug
```

#### Database Debugging

```python
# Enable SQLAlchemy logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

#### API Debugging

```bash
# Test API endpoints
curl -v http://localhost:8000/health/

# Check API logs
docker-compose logs -f api

# Monitor API metrics
curl http://localhost:8000/metrics
```

## Maintenance and Updates

### Regular Maintenance Tasks

#### Database Maintenance

```sql
-- Vacuum and analyze tables
VACUUM ANALYZE;

-- Reindex tables
REINDEX DATABASE nft_trading_bot_prod;

-- Check database size
SELECT pg_size_pretty(pg_database_size('nft_trading_bot_prod'));
```

#### Log Rotation

```bash
# Configure logrotate
cat > /etc/logrotate.d/nft-trading-bot << EOF
/var/log/nft-trading-bot/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 app app
}
EOF
```

#### Backup Procedures

```bash
# Database backup
pg_dump -h localhost -U postgres nft_trading_bot_prod > backup_$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

### Update Procedures

#### Application Updates

```bash
# Zero-downtime deployment
./scripts/deploy.sh production --tag v1.1.0 --run-tests

# Rollback if needed
./scripts/deploy.sh production --tag v1.0.0
```

#### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add new trading features"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

#### Dependency Updates

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Check for security vulnerabilities
pip audit

# Update Docker base image
docker build --no-cache -t nft-trading-bot:latest .
```

### Monitoring and Alerting

#### Health Monitoring

```bash
# Automated health check script
#!/bin/bash
HEALTH_URL="http://localhost:8000/health/"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -ne 200 ]; then
    echo "Health check failed with status $RESPONSE"
    # Send alert
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"NFT Trading Bot health check failed"}' \
        $SLACK_WEBHOOK_URL
fi
```

#### Performance Monitoring

```bash
# Monitor key metrics
#!/bin/bash
# CPU usage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')

# Memory usage
MEM_USAGE=$(free | grep Mem | awk '{printf("%.2f", $3/$2 * 100.0)}')

# Disk usage
DISK_USAGE=$(df -h / | awk 'NR==2{printf "%s", $5}' | sed 's/%//')

echo "CPU: ${CPU_USAGE}%, Memory: ${MEM_USAGE}%, Disk: ${DISK_USAGE}%"
```

---

This deployment guide provides comprehensive coverage of all deployment scenarios. For specific questions or issues not covered here, please refer to the troubleshooting section or contact the development team.

