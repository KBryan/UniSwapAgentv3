"""
Health monitoring endpoints for the NFT-Gated AI Trading Bot.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import time
import psutil
import redis
from datetime import datetime

from config import get_settings
from api.deps import get_redis_client, get_web3_manager, Web3Manager

router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    uptime: float
    services: Dict[str, Any]
    system: Optional[Dict[str, Any]] = None


class ServiceStatus(BaseModel):
    """Individual service status model."""
    status: str
    response_time: Optional[float] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@router.get("/", response_model=HealthResponse)
async def health_check(
    redis_client: redis.Redis = Depends(get_redis_client),
    web3_manager: Web3Manager = Depends(get_web3_manager)
):
    """
    Comprehensive health check endpoint.
    Returns system status, service availability, and performance metrics.
    """
    start_time = time.time()
    
    services = {}
    overall_status = "healthy"
    
    # Check Redis connectivity
    try:
        redis_start = time.time()
        redis_client.ping()
        redis_time = time.time() - redis_start
        services["redis"] = ServiceStatus(
            status="healthy",
            response_time=redis_time,
            details={"connection": "active"}
        )
    except Exception as e:
        services["redis"] = ServiceStatus(
            status="unhealthy",
            error=str(e)
        )
        overall_status = "degraded"
    
    # Check Web3 connections
    web3_services = {}
    for network in ["ethereum", "skale", "beam"]:
        try:
            w3_start = time.time()
            w3 = web3_manager.get_connection(network)
            if w3:
                # Test connection with a simple call
                block_number = w3.eth.block_number
                w3_time = time.time() - w3_start
                web3_services[network] = ServiceStatus(
                    status="healthy",
                    response_time=w3_time,
                    details={"block_number": block_number}
                )
            else:
                web3_services[network] = ServiceStatus(
                    status="unavailable",
                    error="No connection configured"
                )
        except Exception as e:
            web3_services[network] = ServiceStatus(
                status="unhealthy",
                error=str(e)
            )
            if network == "ethereum":  # Ethereum is critical
                overall_status = "degraded"
    
    services["web3"] = web3_services
    
    # Check external APIs (mock for now)
    external_apis = {}
    
    # CoinGecko API check
    try:
        # In a real implementation, you'd make an actual API call
        external_apis["coingecko"] = ServiceStatus(
            status="healthy" if settings.coingecko_api_key else "not_configured",
            details={"configured": bool(settings.coingecko_api_key)}
        )
    except Exception as e:
        external_apis["coingecko"] = ServiceStatus(
            status="unhealthy",
            error=str(e)
        )
    
    # LLM APIs check
    llm_apis = {}
    for provider in ["anthropic", "openai", "gemini", "venice"]:
        api_key_attr = f"{provider}_api_key"
        has_key = bool(getattr(settings, api_key_attr, None))
        llm_apis[provider] = ServiceStatus(
            status="configured" if has_key else "not_configured",
            details={"api_key_configured": has_key}
        )
    
    external_apis["llm"] = llm_apis
    services["external_apis"] = external_apis
    
    # System metrics (optional, for detailed monitoring)
    system_info = None
    if settings.debug:
        try:
            system_info = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except Exception:
            # psutil might not be available in all environments
            pass
    
    total_time = time.time() - start_time
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        uptime=total_time,
        services=services,
        system=system_info
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint for basic availability check."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "message": "pong"
    }


@router.get("/ready")
async def readiness_check(
    redis_client: redis.Redis = Depends(get_redis_client),
    web3_manager: Web3Manager = Depends(get_web3_manager)
):
    """
    Readiness check for Kubernetes/container orchestration.
    Returns 200 if the service is ready to accept traffic.
    """
    try:
        # Check critical dependencies
        redis_client.ping()
        
        # Check if at least Ethereum connection is available
        eth_connection = web3_manager.get_connection("ethereum")
        if not eth_connection:
            raise HTTPException(status_code=503, detail="Ethereum connection not available")
        
        # Test Ethereum connection
        eth_connection.eth.block_number
        
        return {"status": "ready"}
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}"
        )


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration.
    Returns 200 if the service is alive (basic process check).
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow()
    }

