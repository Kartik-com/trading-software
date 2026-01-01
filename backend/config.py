"""
Configuration management for the trading analysis system.
All settings, parameters, and credentials are managed here.
"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Exchange Configuration
EXCHANGE = os.getenv("EXCHANGE", "binance") 
EXCHANGE_TESTNET = os.getenv("EXCHANGE_TESTNET", "false").lower() == "true"

# Trading Pairs to Monitor (Aligned with Binance Liquidity)
SYMBOLS: List[str] = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "BNB/USDT",
]

# Timeframes
TIMEFRAMES = {
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
}

# Primary timeframe for major trend (4-Hour)
TREND_TIMEFRAME = "4h"
# Primary timeframe for bias determination (1-Hour)
# (Used as filter for 15m entries)
BIAS_TIMEFRAME = "1h"
# Entry timeframe for signal generation (15-Minute)
ENTRY_TIMEFRAME = "15m"

# Indicator Parameters
EMA_PERIODS = [20, 50, 100, 200]

# RSI Parameters
RSI_PERIOD = 14
RSI_OVERBOUGHT = 60 # User spec: > 60 is potential sell zone
RSI_OVERSOLD = 40   # User spec: < 40 is potential buy zone
RSI_BUY_MAX = 65    # User spec: Must be < 65 for BUY
RSI_SELL_MIN = 35   # User spec: Must be > 35 for SELL

# Stochastic RSI Parameters
STOCH_RSI_PERIOD = 14
STOCH_RSI_K = 3
STOCH_RSI_D = 3
STOCH_RSI_OVERBOUGHT = 0.8 # User spec: > 0.8
STOCH_RSI_OVERSOLD = 0.2   # User spec: < 0.2
STOCH_BUY_MAX = 0.85       # User spec: Must be < 0.85 for BUY
STOCH_SELL_MIN = 0.15      # User spec: Must be > 0.15 for SELL

# ATR Parameters (for stop loss calculation)
ATR_PERIOD = 14
ATR_MULTIPLIER = 1.5

# Smart Money Concepts Parameters
SWING_LOOKBACK = 3  # Matches user provided script (was 5)
LIQUIDITY_TOLERANCE = 0.001  # 0.1% tolerance for equal highs/lows

# Telegram Configuration (Updated from User Script)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
# TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
TELEGRAM_ENABLED = False # Paused by user request

# Signal Confidence Scoring
# Simple 3-point system from user script:
# - Bias != RANGE (+1)
# - Structure Found (+1)
# - Stoch RSI Extreme (+1)
CONFIDENCE_THRESHOLD_HIGH = 2 # "HIGH" if score >= 2 (max is 3, but script logic says min(score, 2))
MIN_CONFIDENCE_LEVEL = "LOW" # Allow all valid signals through now, since logic is simpler

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# CORS Configuration
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
if _cors_origins == "*":
    CORS_ORIGINS = ["*"]
else:
    CORS_ORIGINS = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]

# Data Configuration
CANDLE_HISTORY_LIMIT = 300  # Number of historical candles to fetch
MIN_CANDLES_FOR_ANALYSIS = 200  # Minimum candles needed for EMA 200
CANDLE_BUFFER_SECONDS = 10 # Buffer to ensure data completeness

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Signal Deduplication
# Prevent duplicate alerts for the same symbol/timeframe within this window
ALERT_COOLDOWN_SECONDS = 60
