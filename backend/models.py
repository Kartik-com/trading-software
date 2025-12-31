"""
Data models and schemas for the trading analysis system.
Uses Pydantic for validation and serialization.
"""
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Candle(BaseModel):
    """OHLCV candle data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MarketStructure(BaseModel):
    """Market structure state tracking"""
    type: Literal["HH", "HL", "LH", "LL", "UNKNOWN"]
    price: float
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MarketBias(BaseModel):
    """Market bias classification"""
    symbol: str
    timeframe: str
    bias: Literal["BULLISH", "BEARISH", "RANGE"]
    price: float
    ema_20: float
    ema_50: float
    ema_100: float
    ema_200: float
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Signal(BaseModel):
    """Trading signal with all metadata"""
    id: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    signal_type: Literal["BUY", "SELL", "REVERSAL"]
    symbol: str
    timeframe: str
    bias: Literal["BULLISH", "BEARISH", "RANGE"]
    structure: str  # e.g., "BOS confirmed", "CHoCH detected"
    entry_price: float
    stop_loss: float
    take_profit: float = 0.0 # Added per user request
    confidence: Literal["LOW", "MEDIUM", "HIGH"]
    candle_close_time: datetime
    
    # Additional metadata
    ema_alignment: bool = False
    rsi: Optional[float] = None
    stoch_rsi_k: Optional[float] = None
    stoch_rsi_d: Optional[float] = None
    liquidity_sweep: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertMessage(BaseModel):
    """Formatted alert message for Telegram"""
    signal: Signal
    
    def format(self) -> str:
        """Format signal matching User Script exactly."""
        emoji_map = {
            "BUY": "🟢",
            "SELL": "🔴",
            "REVERSAL": "🔄"
        }
        
        emoji = emoji_map.get(self.signal.signal_type, "⚪")
        
        # User requested 2 decimal places
        entry = round(self.signal.entry_price, 2)
        sl = round(self.signal.stop_loss, 2)
        tp = round(self.signal.take_profit, 2)
        
        message = (
            f"{emoji} {self.signal.signal_type} SIGNAL — {self.signal.symbol}\n"
            f"Timeframe: {self.signal.timeframe}\n"
            f"Bias (1H): {self.signal.bias}\n"
            f"Structure: {self.signal.structure}\n"
            f"Entry Price: {entry}\n"
            f"Target: {tp}\n"
            f"Stop Loss: {sl}\n"
            f"Confidence: {self.signal.confidence}\n"
            f"Candle Close: {self.signal.candle_close_time.strftime('%Y-%m-%d %H:%M UTC')}"
        )
        
        return message


class PriceData(BaseModel):
    """Current price data for a symbol"""
    symbol: str
    price: float
    change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SignalHistory(BaseModel):
    """Collection of signals"""
    signals: List[Signal]
    total: int
    
    
class PaperTrade(BaseModel):
    """Paper trading position"""
    id: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    symbol: str
    side: Literal["BUY", "SELL"]
    entry_price: float
    stop_loss: float
    take_profit: Optional[float] = None
    quantity: float = 1.0  # Hypothetical quantity
    entry_time: datetime
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    status: Literal["OPEN", "CLOSED_WIN", "CLOSED_LOSS", "CLOSED_MANUAL"] = "OPEN"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaperTradingStats(BaseModel):
    """Paper trading statistics"""
    total_trades: int
    open_trades: int
    closed_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
