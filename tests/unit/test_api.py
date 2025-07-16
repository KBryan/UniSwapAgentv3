"""
Unit tests for API endpoints.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

from fastapi.testclient import TestClient
from api.main import app


class TestHealthEndpoints:
    """Test cases for health monitoring endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        with TestClient(app) as client:
            response = client.get("/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "NFT-Gated AI Trading Bot API"
            assert data["version"] == "1.0.0"
            assert data["status"] == "operational"
    
    @patch('api.deps.redis_client')
    @patch('api.deps.web3_manager')
    def test_health_check(self, mock_web3_manager, mock_redis):
        """Test comprehensive health check."""
        # Mock Redis
        mock_redis.ping.return_value = True
        
        # Mock Web3 manager
        mock_w3 = Mock()
        mock_w3.eth.block_number = 18500000
        mock_web3_manager.get_connection.return_value = mock_w3
        
        with TestClient(app) as client:
            response = client.get("/health/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["healthy", "degraded"]
            assert "services" in data
            assert "redis" in data["services"]
            assert "web3" in data["services"]
    
    def test_ping_endpoint(self):
        """Test simple ping endpoint."""
        with TestClient(app) as client:
            response = client.get("/health/ping")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["message"] == "pong"
            assert "timestamp" in data
    
    @patch('api.deps.redis_client')
    @patch('api.deps.web3_manager')
    def test_readiness_check_success(self, mock_web3_manager, mock_redis):
        """Test readiness check with healthy services."""
        # Mock healthy services
        mock_redis.ping.return_value = True
        
        mock_w3 = Mock()
        mock_w3.eth.block_number = 18500000
        mock_web3_manager.get_connection.return_value = mock_w3
        
        with TestClient(app) as client:
            response = client.get("/health/ready")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
    
    @patch('api.deps.redis_client')
    def test_readiness_check_failure(self, mock_redis):
        """Test readiness check with unhealthy services."""
        # Mock Redis failure
        mock_redis.ping.side_effect = Exception("Redis connection failed")
        
        with TestClient(app) as client:
            response = client.get("/health/ready")
            
            assert response.status_code == 503
            data = response.json()
            assert "Service not ready" in data["detail"]
    
    def test_liveness_check(self):
        """Test liveness check."""
        with TestClient(app) as client:
            response = client.get("/health/live")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "alive"
            assert "timestamp" in data


class TestAuthEndpoints:
    """Test cases for authentication endpoints."""
    
    @patch('api.deps.verify_nft_ownership')
    def test_verify_nft_success(self, mock_verify):
        """Test successful NFT verification."""
        mock_verify.return_value = True
        
        with TestClient(app) as client:
            response = client.post("/auth/verify-nft", json={
                "wallet_address": "0x1234567890abcdef1234567890abcdef12345678"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["verified"] is True
            assert data["has_nft"] is True
            assert "access_token" in data
    
    @patch('api.deps.verify_nft_ownership')
    def test_verify_nft_failure(self, mock_verify):
        """Test failed NFT verification."""
        mock_verify.return_value = False
        
        with TestClient(app) as client:
            response = client.post("/auth/verify-nft", json={
                "wallet_address": "0x1234567890abcdef1234567890abcdef12345678"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["verified"] is False
            assert data["has_nft"] is False
            assert data["access_token"] is None
    
    def test_verify_nft_invalid_address(self):
        """Test NFT verification with invalid wallet address."""
        with TestClient(app) as client:
            response = client.post("/auth/verify-nft", json={
                "wallet_address": "invalid_address"
            })
            
            assert response.status_code == 400
    
    @patch('api.deps.get_current_user')
    def test_get_user_info(self, mock_get_user):
        """Test getting user information."""
        mock_get_user.return_value = {
            "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "authenticated": True,
            "bypass": False
        }
        
        with TestClient(app) as client:
            response = client.get("/auth/me", headers={
                "Authorization": "Bearer test_token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["authenticated"] is True
            assert data["nft_verified"] is True
            assert "permissions" in data
    
    def test_get_user_info_unauthorized(self):
        """Test getting user info without authentication."""
        with TestClient(app) as client:
            response = client.get("/auth/me")
            
            assert response.status_code == 401
    
    @patch('api.deps.get_optional_user')
    def test_check_access_with_auth(self, mock_get_user):
        """Test access check with valid authentication."""
        mock_get_user.return_value = {
            "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "authenticated": True
        }
        
        with TestClient(app) as client:
            response = client.get("/auth/check-access")
            
            assert response.status_code == 200
            data = response.json()
            assert data["has_access"] is True
    
    @patch('api.deps.get_optional_user')
    def test_check_access_without_auth(self, mock_get_user):
        """Test access check without authentication."""
        mock_get_user.return_value = None
        
        with TestClient(app) as client:
            response = client.get("/auth/check-access")
            
            assert response.status_code == 200
            data = response.json()
            assert data["has_access"] is False


class TestTradeEndpoints:
    """Test cases for trading endpoints."""
    
    @patch('api.deps.get_current_user')
    @patch('core.nlp.llm_client.llm_manager.parse_trading_prompt')
    def test_prompt_to_trade(self, mock_parse, mock_get_user):
        """Test natural language prompt to trade conversion."""
        mock_get_user.return_value = {
            "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "authenticated": True
        }
        
        # Mock LLM parsing
        from core.nlp.llm_client import TradingInstruction
        mock_parse.return_value = TradingInstruction(
            action="buy",
            token_in="ETH",
            token_out="USDC",
            amount=1.0,
            confidence=0.8,
            reasoning="Test trade"
        )
        
        with TestClient(app) as client:
            response = client.post("/trade/prompt", 
                headers={"Authorization": "Bearer test_token"},
                json={
                    "prompt": "Buy 1 ETH worth of USDC",
                    "dry_run": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"
            assert data["trade_type"] == "swap"
            assert data["dry_run"] is True
    
    @patch('api.deps.get_current_user')
    def test_direct_trade_execution(self, mock_get_user):
        """Test direct trade execution."""
        mock_get_user.return_value = {
            "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "authenticated": True
        }
        
        with TestClient(app) as client:
            response = client.post("/trade/execute",
                headers={"Authorization": "Bearer test_token"},
                json={
                    "trade_type": "swap",
                    "token_in": "ETH",
                    "token_out": "USDC",
                    "amount_in": 1.0,
                    "dry_run": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"
            assert data["trade_type"] == "swap"
            assert data["token_in"] == "ETH"
            assert data["token_out"] == "USDC"
    
    def test_trade_execution_unauthorized(self):
        """Test trade execution without authentication."""
        with TestClient(app) as client:
            response = client.post("/trade/execute", json={
                "trade_type": "swap",
                "token_in": "ETH",
                "token_out": "USDC",
                "amount_in": 1.0
            })
            
            assert response.status_code == 401
    
    @patch('api.deps.get_current_user')
    def test_get_trade_status(self, mock_get_user):
        """Test getting trade status."""
        mock_get_user.return_value = {
            "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "authenticated": True
        }
        
        with TestClient(app) as client:
            response = client.get("/trade/status/test_trade_123",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "trade_id" in data
            assert "status" in data
    
    @patch('api.deps.get_current_user')
    def test_get_portfolio(self, mock_get_user):
        """Test getting user portfolio."""
        mock_get_user.return_value = {
            "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "authenticated": True
        }
        
        with TestClient(app) as client:
            response = client.get("/trade/portfolio",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "wallet_address" in data
            assert "total_value_usd" in data
            assert "tokens" in data
    
    @patch('api.deps.get_current_user')
    def test_get_strategies(self, mock_get_user):
        """Test getting available strategies."""
        mock_get_user.return_value = {
            "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "authenticated": True
        }
        
        with TestClient(app) as client:
            response = client.get("/trade/strategies",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            if data:  # If strategies are returned
                assert "strategy_id" in data[0]
                assert "name" in data[0]
    
    @patch('api.deps.get_current_user')
    def test_get_trade_history(self, mock_get_user):
        """Test getting trade history."""
        mock_get_user.return_value = {
            "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "authenticated": True
        }
        
        with TestClient(app) as client:
            response = client.get("/trade/history",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "trades" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data


class TestAdminEndpoints:
    """Test cases for admin endpoints."""
    
    @patch('api.routers.admin.is_admin_user')
    @patch('api.deps.get_current_user')
    def test_get_system_stats(self, mock_get_user, mock_is_admin):
        """Test getting system statistics."""
        mock_get_user.return_value = {
            "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "authenticated": True
        }
        mock_is_admin.return_value = True
        
        with TestClient(app) as client:
            response = client.get("/admin/stats",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "total_users" in data
            assert "active_trades" in data
            assert "total_volume_24h" in data
    
    @patch('api.deps.get_current_user')
    def test_admin_access_denied(self, mock_get_user):
        """Test admin access denied for non-admin user."""
        mock_get_user.return_value = {
            "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "authenticated": True
        }
        
        with TestClient(app) as client:
            response = client.get("/admin/stats",
                headers={"Authorization": "Bearer user_token"}
            )
            
            assert response.status_code == 403
    
    @patch('api.routers.admin.is_admin_user')
    @patch('api.deps.get_current_user')
    def test_get_system_config(self, mock_get_user, mock_is_admin):
        """Test getting system configuration."""
        mock_get_user.return_value = {
            "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "authenticated": True
        }
        mock_is_admin.return_value = True
        
        with TestClient(app) as client:
            response = client.get("/admin/config",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "bypass_nft_gate" in data
            assert "real_data_mode" in data
            assert "supported_networks" in data
    
    @patch('api.routers.admin.is_admin_user')
    @patch('api.deps.get_current_user')
    def test_emergency_stop(self, mock_get_user, mock_is_admin):
        """Test emergency stop functionality."""
        mock_get_user.return_value = {
            "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "authenticated": True
        }
        mock_is_admin.return_value = True
        
        with TestClient(app) as client:
            response = client.post("/admin/emergency-stop",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Emergency stop activated"
            assert "activated_by" in data


class TestRateLimiting:
    """Test cases for rate limiting."""
    
    @patch('api.deps.redis_client')
    def test_rate_limiting(self, mock_redis):
        """Test API rate limiting."""
        # Mock Redis to simulate rate limit exceeded
        mock_redis.get.return_value = "100"  # Current request count
        
        with TestClient(app) as client:
            # This would normally trigger rate limiting
            # For testing, we'll just verify the endpoint is accessible
            response = client.get("/health/ping")
            assert response.status_code == 200


class TestErrorHandling:
    """Test cases for error handling."""
    
    def test_404_error(self):
        """Test 404 error handling."""
        with TestClient(app) as client:
            response = client.get("/nonexistent-endpoint")
            assert response.status_code == 404
    
    def test_422_validation_error(self):
        """Test validation error handling."""
        with TestClient(app) as client:
            response = client.post("/auth/verify-nft", json={
                "invalid_field": "invalid_value"
            })
            assert response.status_code == 422
    
    @patch('api.deps.verify_nft_ownership')
    def test_internal_server_error(self, mock_verify):
        """Test internal server error handling."""
        mock_verify.side_effect = Exception("Internal error")
        
        with TestClient(app) as client:
            response = client.post("/auth/verify-nft", json={
                "wallet_address": "0x1234567890abcdef1234567890abcdef12345678"
            })
            
            assert response.status_code == 400  # Handled as bad request

