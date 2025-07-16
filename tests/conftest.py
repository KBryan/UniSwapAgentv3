"""
Pytest configuration and shared fixtures for the NFT-Gated AI Trading Bot tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, Generator
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from core.strategies.base import StrategyConfig, TradingSignal, SignalType, MarketData
from core.execution.engine import TradeExecution, TradeStatus
from integrations.coingecko import CoinData


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock application settings for testing."""
    with patch('config.get_settings') as mock:
        mock.return_value = Mock(
            debug=True,
            bypass_nft_gate=True,
            real_data_mode=False,
            secret_key="test-secret-key",
            database_url="sqlite:///test.db",
            redis_url="redis://localhost:6379/1",
            anthropic_api_key="test-anthropic-key",
            openai_api_key="test-openai-key",
            ethereum_rpc_url="http://localhost:8545",
            private_key="0x" + "0" * 64,
            enable_twitter=False,
            coingecko_api_key="test-coingecko-key",
            max_gas_price=100,
            default_slippage=0.5,
            min_trade_amount=0.001
        )
        yield mock.return_value


@pytest.fixture
def sample_strategy_config():
    """Sample strategy configuration for testing."""
    return StrategyConfig(
        strategy_id="test_momentum_1",
        name="Test Momentum Strategy",
        description="Test momentum strategy for unit tests",
        parameters={
            "lookback_period": 14,
            "momentum_threshold": 0.05,
            "base_trade_amount": 0.1,
            "monitored_tokens": ["ETH", "BTC", "USDC"]
        },
        risk_limits={
            "max_position_size": 0.1,
            "min_confidence": 0.5
        },
        enabled=True
    )


@pytest.fixture
def sample_trading_signal():
    """Sample trading signal for testing."""
    return TradingSignal(
        signal_type=SignalType.BUY,
        token_in="ETH",
        token_out="USDC",
        amount=1.0,
        confidence=0.8,
        timestamp=datetime.utcnow(),
        metadata={
            "momentum_score": 0.7,
            "price": 1600.0,
            "volume_24h": 1000000
        },
        strategy_id="test_momentum_1",
        reason="Strong bullish momentum detected"
    )


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return [
        MarketData(
            symbol="ETH",
            price=1600.0,
            volume_24h=1000000,
            price_change_24h=5.2,
            market_cap=192000000000,
            timestamp=datetime.utcnow()
        ),
        MarketData(
            symbol="BTC",
            price=45000.0,
            volume_24h=2000000,
            price_change_24h=-2.1,
            market_cap=850000000000,
            timestamp=datetime.utcnow()
        )
    ]


@pytest.fixture
def sample_coin_data():
    """Sample CoinGecko coin data for testing."""
    return CoinData(
        id="ethereum",
        symbol="ETH",
        name="Ethereum",
        current_price=1600.0,
        market_cap=192000000000,
        market_cap_rank=2,
        fully_diluted_valuation=192000000000,
        total_volume=1000000,
        high_24h=1650.0,
        low_24h=1550.0,
        price_change_24h=80.0,
        price_change_percentage_24h=5.2,
        market_cap_change_24h=9600000000,
        market_cap_change_percentage_24h=5.2,
        circulating_supply=120000000,
        total_supply=120000000,
        max_supply=None,
        ath=4878.26,
        ath_change_percentage=-67.2,
        ath_date=datetime(2021, 11, 10),
        atl=0.432979,
        atl_change_percentage=369500.0,
        atl_date=datetime(2015, 10, 20),
        last_updated=datetime.utcnow()
    )


@pytest.fixture
def sample_trade_execution():
    """Sample trade execution for testing."""
    signal = TradingSignal(
        signal_type=SignalType.BUY,
        token_in="ETH",
        token_out="USDC",
        amount=1.0,
        confidence=0.8,
        timestamp=datetime.utcnow(),
        metadata={},
        strategy_id="test_strategy",
        reason="Test trade"
    )
    
    return TradeExecution(
        trade_id="test_trade_123",
        signal=signal,
        status=TradeStatus.COMPLETED,
        exchange="uniswap_v3",
        network="ethereum",
        transaction_hash="0x1234567890abcdef",
        block_number=18500000,
        gas_used=150000,
        gas_price=25,
        actual_amount_in=1.0,
        actual_amount_out=1600.0,
        execution_price=1600.0,
        slippage=0.01,
        fees=0.003,
        created_at=datetime.utcnow() - timedelta(minutes=5),
        executed_at=datetime.utcnow()
    )


@pytest.fixture
def mock_web3():
    """Mock Web3 instance for testing."""
    mock_w3 = Mock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.block_number = 18500000
    mock_w3.eth.get_transaction_count.return_value = 42
    mock_w3.to_wei.return_value = 25000000000  # 25 gwei
    mock_w3.to_checksum_address.side_effect = lambda x: x
    
    # Mock contract
    mock_contract = Mock()
    mock_contract.functions.getAmountsOut.return_value.call.return_value = [1000000000000000000, 1600000000]
    mock_w3.eth.contract.return_value = mock_contract
    
    return mock_w3


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.setex.return_value = True
    mock_redis.incr.return_value = 1
    return mock_redis


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "action": "buy",
        "token_in": "ETH",
        "token_out": "USDC",
        "amount": 1.0,
        "amount_type": "absolute",
        "conditions": [],
        "urgency": "normal",
        "confidence": 0.8,
        "reasoning": "Test LLM parsing"
    }


@pytest.fixture
def mock_coingecko_response():
    """Mock CoinGecko API response for testing."""
    return {
        "ethereum": {"usd": 1600.0},
        "bitcoin": {"usd": 45000.0}
    }


@pytest.fixture
def mock_twitter_client():
    """Mock Twitter client for testing."""
    mock_client = Mock()
    mock_client.enabled = True
    mock_client.post_trade_notification = AsyncMock(return_value="tweet_123")
    mock_client.post_strategy_signal = AsyncMock(return_value="tweet_124")
    mock_client.post_market_update = AsyncMock(return_value="tweet_125")
    mock_client.post_system_status = AsyncMock(return_value="tweet_126")
    return mock_client


@pytest.fixture
def authenticated_user():
    """Sample authenticated user for testing."""
    return {
        "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
        "authenticated": True,
        "bypass": False
    }


@pytest.fixture
def bypass_user():
    """Sample bypass user for testing."""
    return {
        "wallet_address": "0x0000000000000000000000000000000000000000",
        "authenticated": True,
        "bypass": True
    }


@pytest.fixture
async def async_client():
    """Async HTTP client for API testing."""
    from httpx import AsyncClient
    from api.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def portfolio_positions():
    """Sample portfolio positions for testing."""
    from core.strategies.base import PortfolioPosition
    
    return [
        PortfolioPosition(
            token="ETH",
            balance=2.5,
            value_usd=4000.0,
            price_usd=1600.0,
            percentage=80.0
        ),
        PortfolioPosition(
            token="USDC",
            balance=1000.0,
            value_usd=1000.0,
            price_usd=1.0,
            percentage=20.0
        )
    ]


# Test data generators
def generate_price_history(symbol: str, days: int = 30, start_price: float = 1000.0):
    """Generate mock price history data."""
    import random
    
    history = []
    current_price = start_price
    
    for i in range(days):
        # Random price movement
        change = random.uniform(-0.05, 0.05)  # ±5% daily change
        current_price *= (1 + change)
        
        history.append({
            "timestamp": datetime.utcnow() - timedelta(days=days-i),
            "price": current_price,
            "volume": random.uniform(500000, 2000000)
        })
    
    return history


def generate_market_data_batch(symbols: list, base_prices: dict = None):
    """Generate batch of market data for multiple symbols."""
    import random
    
    if base_prices is None:
        base_prices = {"ETH": 1600.0, "BTC": 45000.0, "USDC": 1.0}
    
    market_data = []
    
    for symbol in symbols:
        base_price = base_prices.get(symbol, 100.0)
        price_change = random.uniform(-10.0, 10.0)
        
        market_data.append(MarketData(
            symbol=symbol,
            price=base_price * (1 + price_change / 100),
            volume_24h=random.uniform(500000, 5000000),
            price_change_24h=price_change,
            market_cap=base_price * random.uniform(1000000, 100000000),
            timestamp=datetime.utcnow()
        ))
    
    return market_data


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Add any cleanup logic here
    pass

