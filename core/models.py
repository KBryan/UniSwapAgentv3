"""
Database models for NFT Trading Bot.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, 
    ForeignKey, Enum, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .database import Base


class TradeStatus(enum.Enum):
    """Trade execution status."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TradeType(enum.Enum):
    """Type of trade operation."""
    SWAP = "swap"
    BUY = "buy"
    SELL = "sell"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"


class StrategyStatus(enum.Enum):
    """Trading strategy status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"


class User(Base):
    """User model for wallet-based authentication."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String(42), unique=True, index=True, nullable=False)
    nft_verified = Column(Boolean, default=False)
    nft_token_ids = Column(JSON, default=list)  # List of owned NFT token IDs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Relationships
    trades = relationship("Trade", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")
    
    def __repr__(self):
        return f"<User(wallet_address='{self.wallet_address}')>"


class Trade(Base):
    """Trade execution records."""
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Trade details
    trade_type = Column(Enum(TradeType), nullable=False)
    status = Column(Enum(TradeStatus), default=TradeStatus.PENDING)
    
    # Token information
    token_in = Column(String(20), nullable=False)  # e.g., "ETH"
    token_out = Column(String(20), nullable=False)  # e.g., "USDC"
    token_in_address = Column(String(42))  # Contract address
    token_out_address = Column(String(42))  # Contract address
    
    # Amounts
    amount_in = Column(Float, nullable=False)
    amount_out = Column(Float)
    estimated_amount_out = Column(Float)
    
    # Execution details
    execution_price = Column(Float)
    slippage = Column(Float, default=0.5)
    gas_estimate = Column(Integer)
    gas_used = Column(Integer)
    gas_price = Column(Float)
    
    # Blockchain details
    network = Column(String(20), default="ethereum")
    transaction_hash = Column(String(66))
    block_number = Column(Integer)
    
    # Natural language processing
    original_prompt = Column(Text)
    parsed_instruction = Column(JSON)
    confidence_score = Column(Float)
    llm_provider = Column(String(20))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    executed_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Flags
    dry_run = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="trades")
    
    # Indexes
    __table_args__ = (
        Index('ix_trades_user_created', 'user_id', 'created_at'),
        Index('ix_trades_status_created', 'status', 'created_at'),
        Index('ix_trades_token_pair', 'token_in', 'token_out'),
    )
    
    def __repr__(self):
        return f"<Trade(trade_id='{self.trade_id}', status='{self.status}')>"


class Strategy(Base):
    """Trading strategy configurations."""
    
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Strategy details
    name = Column(String(100), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(50), nullable=False)  # e.g., "momentum", "mean_reversion"
    status = Column(Enum(StrategyStatus), default=StrategyStatus.ACTIVE)
    
    # Configuration
    parameters = Column(JSON, default=dict)  # Strategy-specific parameters
    risk_limits = Column(JSON, default=dict)  # Risk management settings
    
    # Performance tracking
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_executed = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="strategies")
    
    def __repr__(self):
        return f"<Strategy(strategy_id='{self.strategy_id}', name='{self.name}')>"


class Portfolio(Base):
    """User portfolio snapshots."""
    
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Portfolio data
    total_value_usd = Column(Float, default=0.0)
    tokens = Column(JSON, default=list)  # List of token holdings
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('ix_portfolios_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Portfolio(user_id={self.user_id}, value=${self.total_value_usd})>"


class MarketData(Base):
    """Market data cache."""
    
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Token information
    symbol = Column(String(20), nullable=False)
    contract_address = Column(String(42))
    network = Column(String(20), default="ethereum")
    
    # Price data
    price_usd = Column(Float, nullable=False)
    price_change_24h = Column(Float, default=0.0)
    volume_24h = Column(Float, default=0.0)
    market_cap = Column(Float)
    
    # Data source
    data_source = Column(String(50), default="coingecko")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('ix_market_data_symbol_updated', 'symbol', 'updated_at'),
        UniqueConstraint('symbol', 'network', name='uq_market_data_symbol_network'),
    )
    
    def __repr__(self):
        return f"<MarketData(symbol='{self.symbol}', price=${self.price_usd})>"


class SystemLog(Base):
    """System audit logs."""
    
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Log details
    level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, etc.
    message = Column(Text, nullable=False)
    category = Column(String(50))  # trade, auth, system, etc.
    
    # Context
    user_id = Column(Integer, ForeignKey("users.id"))
    trade_id = Column(String(50))
    additional_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('ix_system_logs_level_created', 'level', 'created_at'),
        Index('ix_system_logs_category_created', 'category', 'created_at'),
    )
    
    def __repr__(self):
        return f"<SystemLog(level='{self.level}', category='{self.category}')>"


class APIKey(Base):
    """API key management for external services."""
    
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Key details
    service_name = Column(String(50), nullable=False)  # anthropic, openai, etc.
    key_name = Column(String(100))  # Human-readable name
    encrypted_key = Column(Text, nullable=False)  # Encrypted API key
    
    # Status
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))
    
    # Limits
    daily_limit = Column(Integer)
    monthly_limit = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('service_name', 'key_name', name='uq_api_keys_service_name'),
    )
    
    def __repr__(self):
        return f"<APIKey(service='{self.service_name}', name='{self.key_name}')>"

