"""
Unit tests for trading strategies.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from core.strategies.base import (
    BaseStrategy, StrategyRegistry, TradingSignal, SignalType,
    MarketData, PortfolioPosition, StrategyConfig, StrategyStatus
)
from core.strategies.momentum import MomentumStrategy


class TestBaseStrategy:
    """Test cases for BaseStrategy abstract class."""
    
    def test_strategy_initialization(self, sample_strategy_config):
        """Test strategy initialization."""
        
        class TestStrategy(BaseStrategy):
            async def analyze_market(self, market_data):
                return None
            
            async def validate_signal(self, signal, portfolio):
                return True
            
            def get_required_data(self):
                return ["ETH", "BTC"]
        
        strategy = TestStrategy(sample_strategy_config)
        
        assert strategy.config == sample_strategy_config
        assert strategy.status == StrategyStatus.INACTIVE
        assert strategy.last_signal is None
        assert strategy.performance_metrics == {}
    
    @pytest.mark.asyncio
    async def test_strategy_lifecycle(self, sample_strategy_config):
        """Test strategy start/stop/pause/resume lifecycle."""
        
        class TestStrategy(BaseStrategy):
            async def analyze_market(self, market_data):
                return None
            
            async def validate_signal(self, signal, portfolio):
                return True
            
            def get_required_data(self):
                return ["ETH"]
        
        strategy = TestStrategy(sample_strategy_config)
        
        # Test start
        await strategy.start()
        assert strategy.status == StrategyStatus.ACTIVE
        
        # Test pause
        await strategy.pause()
        assert strategy.status == StrategyStatus.PAUSED
        
        # Test resume
        await strategy.resume()
        assert strategy.status == StrategyStatus.ACTIVE
        
        # Test stop
        await strategy.stop()
        assert strategy.status == StrategyStatus.INACTIVE
    
    def test_risk_limits_check(self, sample_strategy_config, sample_trading_signal, portfolio_positions):
        """Test risk limits checking."""
        
        class TestStrategy(BaseStrategy):
            async def analyze_market(self, market_data):
                return None
            
            async def validate_signal(self, signal, portfolio):
                return True
            
            def get_required_data(self):
                return ["ETH"]
        
        strategy = TestStrategy(sample_strategy_config)
        
        # Test within risk limits
        sample_trading_signal.confidence = 0.8  # Above min_confidence (0.5)
        assert strategy.check_risk_limits(sample_trading_signal, portfolio_positions)
        
        # Test below confidence threshold
        sample_trading_signal.confidence = 0.3  # Below min_confidence (0.5)
        assert not strategy.check_risk_limits(sample_trading_signal, portfolio_positions)
    
    def test_performance_metrics(self, sample_strategy_config):
        """Test performance metrics management."""
        
        class TestStrategy(BaseStrategy):
            async def analyze_market(self, market_data):
                return None
            
            async def validate_signal(self, signal, portfolio):
                return True
            
            def get_required_data(self):
                return ["ETH"]
        
        strategy = TestStrategy(sample_strategy_config)
        
        # Test initial metrics
        assert strategy.get_performance_metrics() == {}
        
        # Test updating metrics
        metrics = {"total_trades": 10, "win_rate": 0.7, "total_pnl": 1500.0}
        strategy.update_performance_metrics(metrics)
        
        assert strategy.get_performance_metrics() == metrics
        
        # Test updating additional metrics
        new_metrics = {"sharpe_ratio": 1.5}
        strategy.update_performance_metrics(new_metrics)
        
        expected = {**metrics, **new_metrics}
        assert strategy.get_performance_metrics() == expected


class TestMomentumStrategy:
    """Test cases for MomentumStrategy."""
    
    def test_momentum_strategy_initialization(self, sample_strategy_config):
        """Test momentum strategy initialization."""
        strategy = MomentumStrategy(sample_strategy_config)
        
        assert strategy.lookback_period == 14
        assert strategy.momentum_threshold == 0.05
        assert strategy.price_history == {}
        assert strategy.volume_history == {}
        assert strategy.last_signals == {}
    
    @pytest.mark.asyncio
    async def test_analyze_market_insufficient_data(self, sample_strategy_config, sample_market_data):
        """Test market analysis with insufficient historical data."""
        strategy = MomentumStrategy(sample_strategy_config)
        
        # With no price history, should return None
        signal = await strategy.analyze_market(sample_market_data)
        assert signal is None
    
    @pytest.mark.asyncio
    async def test_analyze_market_with_history(self, sample_strategy_config):
        """Test market analysis with sufficient historical data."""
        strategy = MomentumStrategy(sample_strategy_config)
        
        # Populate price history
        eth_prices = [1500.0 + i * 10 for i in range(25)]  # Upward trend
        strategy.price_history["ETH"] = eth_prices
        strategy.volume_history["ETH"] = [1000000] * 25
        
        market_data = [MarketData(
            symbol="ETH",
            price=1750.0,
            volume_24h=1200000,  # Above average volume
            price_change_24h=5.0,
            timestamp=datetime.utcnow()
        )]
        
        signal = await strategy.analyze_market(market_data)
        
        # Should generate a buy signal due to upward momentum
        assert signal is not None
        assert signal.signal_type == SignalType.BUY
        assert signal.token_in == "ETH"
        assert signal.confidence > 0
    
    def test_momentum_score_calculation(self, sample_strategy_config):
        """Test momentum score calculation."""
        strategy = MomentumStrategy(sample_strategy_config)
        
        # Test upward momentum
        upward_prices = [1000.0, 1050.0, 1100.0, 1150.0, 1200.0, 1250.0, 1300.0, 1350.0, 1400.0, 1450.0, 1500.0, 1550.0, 1600.0, 1650.0, 1700.0]
        momentum_score = strategy._calculate_momentum_score(upward_prices)
        assert momentum_score > 0  # Positive momentum
        
        # Test downward momentum
        downward_prices = [1700.0, 1650.0, 1600.0, 1550.0, 1500.0, 1450.0, 1400.0, 1350.0, 1300.0, 1250.0, 1200.0, 1150.0, 1100.0, 1050.0, 1000.0]
        momentum_score = strategy._calculate_momentum_score(downward_prices)
        assert momentum_score < 0  # Negative momentum
        
        # Test sideways movement
        sideways_prices = [1500.0] * 15
        momentum_score = strategy._calculate_momentum_score(sideways_prices)
        assert abs(momentum_score) < 0.1  # Near zero momentum
    
    def test_ma_crossover_calculation(self, sample_strategy_config):
        """Test moving average crossover calculation."""
        strategy = MomentumStrategy(sample_strategy_config)
        
        # Test bullish crossover (short MA crosses above long MA)
        # Create price pattern where short MA will cross above long MA
        prices = [1000.0] * 15 + [1100.0] * 10  # Price jump
        ma_signal = strategy._calculate_ma_crossover(prices)
        assert ma_signal == 1  # Bullish crossover
        
        # Test bearish crossover
        prices = [1100.0] * 15 + [1000.0] * 10  # Price drop
        ma_signal = strategy._calculate_ma_crossover(prices)
        assert ma_signal == -1  # Bearish crossover
    
    def test_volume_confirmation(self, sample_strategy_config):
        """Test volume confirmation logic."""
        strategy = MomentumStrategy(sample_strategy_config)
        
        # Test with high volume
        volumes = [1000000] * 14
        current_volume = 1500000  # 50% above average
        confirmation = strategy._check_volume_confirmation(volumes, current_volume)
        assert confirmation is True
        
        # Test with low volume
        current_volume = 500000  # Below threshold
        confirmation = strategy._check_volume_confirmation(volumes, current_volume)
        assert confirmation is False
    
    def test_signal_type_determination(self, sample_strategy_config):
        """Test signal type determination logic."""
        strategy = MomentumStrategy(sample_strategy_config)
        
        # Test buy signal
        signal_type = strategy._determine_signal_type(
            momentum_score=0.1,  # Above threshold
            ma_signal=1,  # Bullish crossover
            volume_confirmation=True
        )
        assert signal_type == SignalType.BUY
        
        # Test sell signal
        signal_type = strategy._determine_signal_type(
            momentum_score=-0.1,  # Below negative threshold
            ma_signal=-1,  # Bearish crossover
            volume_confirmation=True
        )
        assert signal_type == SignalType.SELL
        
        # Test hold signal
        signal_type = strategy._determine_signal_type(
            momentum_score=0.02,  # Below threshold
            ma_signal=0,  # No crossover
            volume_confirmation=False
        )
        assert signal_type == SignalType.HOLD
    
    @pytest.mark.asyncio
    async def test_validate_signal(self, sample_strategy_config, sample_trading_signal, portfolio_positions):
        """Test signal validation."""
        strategy = MomentumStrategy(sample_strategy_config)
        
        # Test valid signal
        sample_trading_signal.metadata["momentum_score"] = 0.1  # Above threshold
        is_valid = await strategy.validate_signal(sample_trading_signal, portfolio_positions)
        assert is_valid is True
        
        # Test weak momentum signal
        sample_trading_signal.metadata["momentum_score"] = 0.02  # Below threshold
        is_valid = await strategy.validate_signal(sample_trading_signal, portfolio_positions)
        assert is_valid is False
    
    def test_required_data(self, sample_strategy_config):
        """Test required data specification."""
        strategy = MomentumStrategy(sample_strategy_config)
        
        required_data = strategy.get_required_data()
        assert isinstance(required_data, list)
        assert len(required_data) > 0
        assert "ETH" in required_data


class TestStrategyRegistry:
    """Test cases for StrategyRegistry."""
    
    def test_registry_initialization(self):
        """Test strategy registry initialization."""
        registry = StrategyRegistry()
        
        assert registry._strategies == {}
        assert registry._strategy_classes == {}
    
    def test_register_strategy_class(self):
        """Test strategy class registration."""
        registry = StrategyRegistry()
        
        # Test valid registration
        registry.register_strategy_class("momentum", MomentumStrategy)
        assert "momentum" in registry._strategy_classes
        assert registry._strategy_classes["momentum"] == MomentumStrategy
        
        # Test invalid registration
        with pytest.raises(ValueError):
            registry.register_strategy_class("invalid", str)  # Not a BaseStrategy subclass
    
    def test_create_strategy(self, sample_strategy_config):
        """Test strategy creation."""
        registry = StrategyRegistry()
        registry.register_strategy_class("momentum", MomentumStrategy)
        
        # Test valid creation
        strategy = registry.create_strategy("momentum", sample_strategy_config)
        assert isinstance(strategy, MomentumStrategy)
        assert strategy.config == sample_strategy_config
        assert sample_strategy_config.strategy_id in registry._strategies
        
        # Test invalid strategy type
        with pytest.raises(ValueError):
            registry.create_strategy("unknown", sample_strategy_config)
    
    def test_strategy_management(self, sample_strategy_config):
        """Test strategy management operations."""
        registry = StrategyRegistry()
        registry.register_strategy_class("momentum", MomentumStrategy)
        
        # Create strategy
        strategy = registry.create_strategy("momentum", sample_strategy_config)
        strategy_id = sample_strategy_config.strategy_id
        
        # Test get strategy
        retrieved = registry.get_strategy(strategy_id)
        assert retrieved == strategy
        
        # Test list strategies
        all_strategies = registry.list_strategies()
        assert len(all_strategies) == 1
        assert strategy in all_strategies
        
        # Test list active strategies (initially none)
        active_strategies = registry.list_active_strategies()
        assert len(active_strategies) == 0
        
        # Start strategy and test active list
        strategy.status = StrategyStatus.ACTIVE
        active_strategies = registry.list_active_strategies()
        assert len(active_strategies) == 1
        assert strategy in active_strategies
        
        # Test remove strategy
        removed = registry.remove_strategy(strategy_id)
        assert removed is True
        assert registry.get_strategy(strategy_id) is None
        
        # Test remove non-existent strategy
        removed = registry.remove_strategy("non_existent")
        assert removed is False
    
    @pytest.mark.asyncio
    async def test_start_stop_all_strategies(self, sample_strategy_config):
        """Test starting and stopping all strategies."""
        registry = StrategyRegistry()
        registry.register_strategy_class("momentum", MomentumStrategy)
        
        # Create multiple strategies
        config1 = sample_strategy_config
        config2 = StrategyConfig(
            strategy_id="test_momentum_2",
            name="Test Momentum Strategy 2",
            description="Second test strategy",
            parameters={},
            risk_limits={},
            enabled=True
        )
        
        strategy1 = registry.create_strategy("momentum", config1)
        strategy2 = registry.create_strategy("momentum", config2)
        
        # Test start all
        await registry.start_all_strategies()
        assert strategy1.status == StrategyStatus.ACTIVE
        assert strategy2.status == StrategyStatus.ACTIVE
        
        # Test stop all
        await registry.stop_all_strategies()
        assert strategy1.status == StrategyStatus.INACTIVE
        assert strategy2.status == StrategyStatus.INACTIVE
    
    def test_get_available_strategy_types(self):
        """Test getting available strategy types."""
        registry = StrategyRegistry()
        
        # Initially empty
        types = registry.get_available_strategy_types()
        assert types == []
        
        # After registration
        registry.register_strategy_class("momentum", MomentumStrategy)
        types = registry.get_available_strategy_types()
        assert "momentum" in types

