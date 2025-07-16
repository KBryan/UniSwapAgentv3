"""
Trade execution engine for the NFT-Gated AI Trading Bot.
Handles trade execution across different exchanges and networks.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import logging
import asyncio
from decimal import Decimal

from config import get_settings, SUPPORTED_EXCHANGES
from core.strategies.base import TradingSignal, SignalType

logger = logging.getLogger(__name__)
settings = get_settings()


class TradeStatus(str, Enum):
    """Trade execution status."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionError(Exception):
    """Custom exception for trade execution errors."""
    pass


@dataclass
class TradeExecution:
    """Represents a trade execution."""
    trade_id: str
    signal: TradingSignal
    status: TradeStatus
    exchange: str
    network: str
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    gas_price: Optional[int] = None
    actual_amount_in: Optional[float] = None
    actual_amount_out: Optional[float] = None
    execution_price: Optional[float] = None
    slippage: Optional[float] = None
    fees: Optional[float] = None
    created_at: datetime = None
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class TradeQuote:
    """Represents a trade quote from an exchange."""
    exchange: str
    token_in: str
    token_out: str
    amount_in: float
    amount_out: float
    price: float
    gas_estimate: int
    slippage: float
    fees: float
    valid_until: datetime
    route: Optional[List[str]] = None


class ExchangeAdapter(ABC):
    """
    Abstract base class for exchange adapters.
    
    Each exchange (Uniswap, SushiSwap, etc.) implements this interface
    to provide unified trading functionality.
    """
    
    def __init__(self, network: str):
        self.network = network
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def get_quote(self, token_in: str, token_out: str, amount_in: float) -> TradeQuote:
        """
        Get a quote for a trade.
        
        Args:
            token_in: Input token address or symbol
            token_out: Output token address or symbol
            amount_in: Amount of input token
            
        Returns:
            TradeQuote with execution details
        """
        pass
    
    @abstractmethod
    async def execute_trade(self, quote: TradeQuote, wallet_address: str, slippage: float) -> str:
        """
        Execute a trade based on a quote.
        
        Args:
            quote: Trade quote to execute
            wallet_address: Wallet address for execution
            slippage: Maximum slippage tolerance
            
        Returns:
            Transaction hash
        """
        pass
    
    @abstractmethod
    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction status and details.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction status and details
        """
        pass
    
    @abstractmethod
    async def estimate_gas(self, token_in: str, token_out: str, amount_in: float) -> int:
        """
        Estimate gas cost for a trade.
        
        Args:
            token_in: Input token
            token_out: Output token
            amount_in: Input amount
            
        Returns:
            Estimated gas units
        """
        pass


class TradeExecutionEngine:
    """
    Main trade execution engine.
    
    Coordinates trade execution across multiple exchanges and networks,
    handles routing, and manages execution state.
    """
    
    def __init__(self):
        self.adapters: Dict[str, ExchangeAdapter] = {}
        self.active_trades: Dict[str, TradeExecution] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_adapter(self, exchange: str, adapter: ExchangeAdapter):
        """
        Register an exchange adapter.
        
        Args:
            exchange: Exchange name
            adapter: Exchange adapter instance
        """
        self.adapters[exchange] = adapter
        self.logger.info(f"Registered adapter for {exchange}")
    
    async def get_best_quote(self, 
                           token_in: str, 
                           token_out: str, 
                           amount_in: float,
                           exchanges: Optional[List[str]] = None) -> Optional[TradeQuote]:
        """
        Get the best quote across multiple exchanges.
        
        Args:
            token_in: Input token
            token_out: Output token
            amount_in: Input amount
            exchanges: List of exchanges to check (optional)
            
        Returns:
            Best trade quote or None if no quotes available
        """
        if exchanges is None:
            exchanges = list(self.adapters.keys())
        
        quotes = []
        
        # Get quotes from all available exchanges
        for exchange in exchanges:
            if exchange not in self.adapters:
                continue
            
            try:
                adapter = self.adapters[exchange]
                quote = await adapter.get_quote(token_in, token_out, amount_in)
                quotes.append(quote)
                
            except Exception as e:
                self.logger.warning(f"Failed to get quote from {exchange}: {e}")
        
        if not quotes:
            return None
        
        # Find best quote (highest output amount after fees)
        best_quote = max(quotes, key=lambda q: q.amount_out - q.fees)
        
        self.logger.info(f"Best quote: {best_quote.exchange} - {best_quote.amount_out} {token_out}")
        
        return best_quote
    
    async def execute_signal(self, 
                           signal: TradingSignal, 
                           wallet_address: str,
                           exchange: Optional[str] = None,
                           max_slippage: float = 0.5,
                           dry_run: bool = False) -> TradeExecution:
        """
        Execute a trading signal.
        
        Args:
            signal: Trading signal to execute
            wallet_address: Wallet address for execution
            exchange: Specific exchange to use (optional)
            max_slippage: Maximum slippage tolerance
            dry_run: Execute as simulation
            
        Returns:
            TradeExecution with execution details
        """
        trade_id = f"trade_{int(datetime.utcnow().timestamp())}"
        
        execution = TradeExecution(
            trade_id=trade_id,
            signal=signal,
            status=TradeStatus.PENDING,
            exchange=exchange or "auto",
            network="ethereum",  # Default network
            created_at=datetime.utcnow()
        )
        
        self.active_trades[trade_id] = execution
        
        try:
            # Convert signal to trade parameters
            token_in, token_out, amount_in = self._signal_to_trade_params(signal)
            
            # Get best quote if exchange not specified
            if exchange is None:
                quote = await self.get_best_quote(token_in, token_out, amount_in)
                if not quote:
                    raise ExecutionError("No quotes available for trade")
                exchange = quote.exchange
            else:
                if exchange not in self.adapters:
                    raise ExecutionError(f"Exchange {exchange} not available")
                quote = await self.adapters[exchange].get_quote(token_in, token_out, amount_in)
            
            execution.exchange = exchange
            
            # Validate quote against slippage limits
            if quote.slippage > max_slippage:
                raise ExecutionError(f"Slippage too high: {quote.slippage:.2%} > {max_slippage:.2%}")
            
            # Execute trade if not dry run
            if not dry_run and not settings.bypass_nft_gate:
                execution.status = TradeStatus.SUBMITTED
                
                adapter = self.adapters[exchange]
                tx_hash = await adapter.execute_trade(quote, wallet_address, max_slippage)
                
                execution.transaction_hash = tx_hash
                execution.status = TradeStatus.CONFIRMED
                
                # Monitor transaction
                await self._monitor_transaction(execution)
                
            else:
                # Simulate execution
                execution.status = TradeStatus.COMPLETED
                execution.actual_amount_in = quote.amount_in
                execution.actual_amount_out = quote.amount_out
                execution.execution_price = quote.price
                execution.slippage = quote.slippage
                execution.fees = quote.fees
                execution.gas_used = quote.gas_estimate
                execution.executed_at = datetime.utcnow()
                
                self.logger.info(f"Simulated trade execution: {trade_id}")
            
            return execution
            
        except Exception as e:
            execution.status = TradeStatus.FAILED
            execution.error_message = str(e)
            self.logger.error(f"Trade execution failed: {e}")
            return execution
    
    def _signal_to_trade_params(self, signal: TradingSignal) -> Tuple[str, str, float]:
        """
        Convert trading signal to trade parameters.
        
        Args:
            signal: Trading signal
            
        Returns:
            Tuple of (token_in, token_out, amount_in)
        """
        if signal.signal_type == SignalType.BUY:
            return signal.token_in, signal.token_out, signal.amount
        elif signal.signal_type == SignalType.SELL:
            return signal.token_in, signal.token_out, signal.amount
        else:
            raise ExecutionError(f"Unsupported signal type: {signal.signal_type}")
    
    async def _monitor_transaction(self, execution: TradeExecution):
        """
        Monitor transaction execution and update status.
        
        Args:
            execution: Trade execution to monitor
        """
        if not execution.transaction_hash:
            return
        
        adapter = self.adapters[execution.exchange]
        max_attempts = 60  # 5 minutes with 5-second intervals
        
        for attempt in range(max_attempts):
            try:
                tx_status = await adapter.get_transaction_status(execution.transaction_hash)
                
                if tx_status.get("status") == "success":
                    execution.status = TradeStatus.COMPLETED
                    execution.block_number = tx_status.get("block_number")
                    execution.gas_used = tx_status.get("gas_used")
                    execution.actual_amount_out = tx_status.get("amount_out")
                    execution.executed_at = datetime.utcnow()
                    
                    self.logger.info(f"Trade completed: {execution.trade_id}")
                    break
                    
                elif tx_status.get("status") == "failed":
                    execution.status = TradeStatus.FAILED
                    execution.error_message = tx_status.get("error", "Transaction failed")
                    
                    self.logger.error(f"Trade failed: {execution.trade_id}")
                    break
                
                # Wait before next check
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.warning(f"Error monitoring transaction: {e}")
                await asyncio.sleep(5)
        
        # Timeout handling
        if execution.status == TradeStatus.CONFIRMED:
            execution.status = TradeStatus.FAILED
            execution.error_message = "Transaction monitoring timeout"
            self.logger.error(f"Transaction monitoring timeout: {execution.trade_id}")
    
    async def cancel_trade(self, trade_id: str) -> bool:
        """
        Cancel a pending trade.
        
        Args:
            trade_id: Trade ID to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        if trade_id not in self.active_trades:
            return False
        
        execution = self.active_trades[trade_id]
        
        if execution.status in [TradeStatus.COMPLETED, TradeStatus.FAILED, TradeStatus.CANCELLED]:
            return False
        
        execution.status = TradeStatus.CANCELLED
        self.logger.info(f"Trade cancelled: {trade_id}")
        
        return True
    
    def get_trade_status(self, trade_id: str) -> Optional[TradeExecution]:
        """
        Get trade execution status.
        
        Args:
            trade_id: Trade ID
            
        Returns:
            TradeExecution or None if not found
        """
        return self.active_trades.get(trade_id)
    
    def list_active_trades(self) -> List[TradeExecution]:
        """
        Get list of active trades.
        
        Returns:
            List of active trade executions
        """
        return [
            execution for execution in self.active_trades.values()
            if execution.status in [TradeStatus.PENDING, TradeStatus.SUBMITTED, TradeStatus.CONFIRMED]
        ]
    
    def get_trade_history(self, limit: int = 50) -> List[TradeExecution]:
        """
        Get trade execution history.
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trade executions
        """
        all_trades = list(self.active_trades.values())
        all_trades.sort(key=lambda t: t.created_at, reverse=True)
        
        return all_trades[:limit]


# Global trade execution engine instance
trade_engine = TradeExecutionEngine()

