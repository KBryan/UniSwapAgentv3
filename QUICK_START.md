# Quick Start Guide

This guide will get you up and running with the NFT-Gated AI Trading Bot in under 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)

## 1. Extract and Setup

```bash
# Extract the system
tar -xzf nft-trading-bot-complete-system.tar.gz
cd nft-trading-bot

# The .env file is already included with default values
# No additional configuration needed for basic testing
```

## 2. Start the System

```bash
# Start all services with Docker Compose
docker-compose up --build

# Or run in background
docker-compose up -d --build

# Wait for services to start (about 30 seconds)
sleep 30

# Initialize the database (run this once)
python3 scripts/init-db.py
```

**Alternative: Manual database setup**
```bash
# If the script doesn't work, you can run migrations manually
python3 -m alembic upgrade head
```

## 3. Verify Installation

Once the services are running, verify the installation:

```bash
# Check API health
curl http://localhost:8000/health/

# View API documentation
open http://localhost:8000/docs
```

## 4. Test the System

### Basic Health Check
```bash
curl http://localhost:8000/health/
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "web3": {"status": "healthy"}
  }
}
```

### Test NFT Verification (Bypass Mode)
```bash
curl -X POST "http://localhost:8000/auth/verify-nft" \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0x1234567890abcdef1234567890abcdef12345678"}'
```

Expected response:
```json
{
  "verified": true,
  "has_nft": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Test Natural Language Trading (Mock Mode)
```bash
# First get a token (from previous step)
TOKEN="your-token-here"

# Test trading prompt
curl -X POST "http://localhost:8000/trade/prompt" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Buy 1 ETH with USDC", "dry_run": true}'
```

## 5. Access Points

Once running, you can access:

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Celery Monitor**: http://localhost:5555
- **Health Check**: http://localhost:8000/health/

## 6. Default Configuration

The included `.env` file has these key settings for immediate testing:

- `DEBUG=true` - Detailed error messages
- `BYPASS_NFT_GATE=true` - Skip NFT verification for testing
- `REAL_DATA_MODE=false` - Use mock data instead of real market data
- `MOCK_EXTERNAL_SERVICES=true` - Mock external API calls

## 7. Customization

To customize for your needs:

1. **Edit the .env file**:
   ```bash
   nano .env
   ```

2. **Key settings to change**:
   - `ETHEREUM_RPC_URL` - Your Ethereum RPC provider
   - `ANTHROPIC_API_KEY` - Your Anthropic API key
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `PRIVATE_KEY` - Your trading wallet private key
   - `NFT_CONTRACT_ADDRESS` - Your NFT contract for gating

3. **Restart the services**:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

## 8. Production Setup

For production deployment:

1. **Copy production template**:
   ```bash
   cp .env.production.template .env.production
   ```

2. **Edit production settings**:
   ```bash
   nano .env.production
   ```

3. **Deploy with production config**:
   ```bash
   ./scripts/deploy.sh production --build --tag v1.0.0
   ```

## Troubleshooting

### Common Issues

1. **Port conflicts**: If port 8000 is in use, change it in docker-compose.yml
2. **Database connection**: Ensure PostgreSQL container is running
3. **Redis connection**: Ensure Redis container is running

### Check Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs api
docker-compose logs worker
docker-compose logs postgres
```

### Reset Everything

```bash
# Stop and remove all containers and volumes
docker-compose down -v

# Rebuild and start fresh
docker-compose up --build
```

## Next Steps

1. **Read the full documentation**: Check `README.md` and `docs/` folder
2. **Configure real API keys**: Update `.env` with your actual API keys
3. **Set up monitoring**: Configure Prometheus and Grafana
4. **Deploy to production**: Use the deployment guide for your platform

## Support

- **Documentation**: See `docs/` folder for detailed guides
- **API Reference**: http://localhost:8000/docs
- **Issues**: Check logs and troubleshooting section

The system is now ready for development and testing!

