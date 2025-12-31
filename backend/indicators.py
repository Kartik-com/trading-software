"""
Technical indicator calculations for market analysis.
All calculations use pandas for efficiency and accuracy.
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
import config


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average.
    
    Args:
        data: Price series (typically close prices)
        period: EMA period
        
    Returns:
        Series with EMA values
    """
    return data.ewm(span=period, adjust=False).mean()


def calculate_all_emas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all configured EMAs and add them to the dataframe.
    
    Args:
        df: DataFrame with OHLCV data (must have 'close' column)
        
    Returns:
        DataFrame with EMA columns added
    """
    df = df.copy()
    
    for period in config.EMA_PERIODS:
        df[f'ema_{period}'] = calculate_ema(df['close'], period)
    
    return df


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index.
    
    Args:
        data: Price series
        period: RSI period (default 14)
        
    Returns:
        Series with RSI values (0-100)
    """
    delta = data.diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_stochastic_rsi(
    df: pd.DataFrame,
    rsi_period: int = None,
    stoch_period: int = 14,
    k_period: int = None,
    d_period: int = None
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Stochastic RSI indicator.
    
    Args:
        df: DataFrame with OHLCV data
        rsi_period: RSI calculation period (default from config)
        stoch_period: Stochastic calculation period
        k_period: %K smoothing period (default from config)
        d_period: %D smoothing period (default from config)
        
    Returns:
        Tuple of (K line, D line) as Series
    """
    # Use config defaults if not provided
    rsi_period = rsi_period or config.STOCH_RSI_PERIOD
    k_period = k_period or config.STOCH_RSI_K
    d_period = d_period or config.STOCH_RSI_D
    
    # Calculate RSI
    rsi = calculate_rsi(df['close'], rsi_period)
    
    # Calculate Stochastic of RSI
    rsi_min = rsi.rolling(window=stoch_period).min()
    rsi_max = rsi.rolling(window=stoch_period).max()
    
    stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min) * 100
    
    # Smooth to get %K
    k_line = stoch_rsi.rolling(window=k_period).mean()
    
    # Smooth %K to get %D
    d_line = k_line.rolling(window=d_period).mean()
    
    return k_line, d_line


def calculate_atr(df: pd.DataFrame, period: int = None) -> pd.Series:
    """
    Calculate Average True Range for volatility measurement.
    Used for stop loss calculation.
    
    Args:
        df: DataFrame with OHLCV data
        period: ATR period (default from config)
        
    Returns:
        Series with ATR values
    """
    period = period or config.ATR_PERIOD
    
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range calculation
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Average True Range
    atr = tr.rolling(window=period).mean()
    
    return atr


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all technical indicators to the dataframe.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with all indicators added
    """
    df = df.copy()
    
    # Add EMAs
    df = calculate_all_emas(df)
    
    # Add RSI (Required for strict filtering)
    df['rsi'] = calculate_rsi(df['close'], config.RSI_PERIOD)
    
    # Add Stochastic RSI
    k_line, d_line = calculate_stochastic_rsi(df)
    df['stoch_rsi_k'] = k_line
    df['stoch_rsi_d'] = d_line
    
    # Add ATR
    df['atr'] = calculate_atr(df)
    
    return df


def is_ema_bullish_aligned(row: pd.Series) -> bool:
    """
    Check if EMAs are in bullish alignment.
    Bullish: price > EMA20 > EMA50 (and ideally > EMA100/200)
    
    Args:
        row: DataFrame row with price and EMA columns
        
    Returns:
        True if bullish aligned
    """
    try:
        price = row['close']
        ema_20 = row['ema_20']
        ema_50 = row['ema_50']
        
        # Basic bullish alignment: price above key EMAs
        return price > ema_20 and price > ema_50
    except KeyError:
        return False


def is_ema_bearish_aligned(row: pd.Series) -> bool:
    """
    Check if EMAs are in bearish alignment.
    Bearish: price < EMA20 < EMA50 (and ideally < EMA100/200)
    
    Args:
        row: DataFrame row with price and EMA columns
        
    Returns:
        True if bearish aligned
    """
    try:
        price = row['close']
        ema_20 = row['ema_20']
        ema_50 = row['ema_50']
        
        # Basic bearish alignment: price below key EMAs
        return price < ema_20 and price < ema_50
    except KeyError:
        return False


def get_market_bias(df: pd.DataFrame) -> str:
    """
    Determine overall market bias based on EMA alignment.
    
    Args:
        df: DataFrame with indicators
        
    Returns:
        "BULLISH", "BEARISH", or "RANGE"
    """
    if len(df) < 2:
        return "RANGE"
    
    latest = df.iloc[-1]
    
    if is_ema_bullish_aligned(latest):
        return "BULLISH"
    elif is_ema_bearish_aligned(latest):
        return "BEARISH"
    else:
        return "RANGE"


def is_stoch_rsi_oversold_recovery(k: float, d: float, prev_k: float, prev_d: float) -> bool:
    """
    Check if Stochastic RSI shows oversold recovery.
    Signal: K crosses above D in oversold zone (below 20)
    
    Args:
        k: Current K value
        d: Current D value
        prev_k: Previous K value
        prev_d: Previous D value
        
    Returns:
        True if oversold recovery detected
    """
    if pd.isna(k) or pd.isna(d) or pd.isna(prev_k) or pd.isna(prev_d):
        return False
    
    # K was below D, now above D
    crossover = prev_k <= prev_d and k > d
    
    # In or recently in oversold zone
    oversold = k < config.STOCH_RSI_OVERSOLD or prev_k < config.STOCH_RSI_OVERSOLD
    
    return crossover and oversold


def is_stoch_rsi_overbought_decline(k: float, d: float, prev_k: float, prev_d: float) -> bool:
    """
    Check if Stochastic RSI shows overbought decline.
    Signal: K crosses below D in overbought zone (above 80)
    
    Args:
        k: Current K value
        d: Current D value
        prev_k: Previous K value
        prev_d: Previous D value
        
    Returns:
        True if overbought decline detected
    """
    if pd.isna(k) or pd.isna(d) or pd.isna(prev_k) or pd.isna(prev_d):
        return False
    
    # K was above D, now below D
    crossunder = prev_k >= prev_d and k < d
    
    # In or recently in overbought zone
    overbought = k > config.STOCH_RSI_OVERBOUGHT or prev_k > config.STOCH_RSI_OVERBOUGHT
    
    return crossunder and overbought


def calculate_stop_loss(
    df: pd.DataFrame,
    signal_type: str,
    entry_price: float
) -> float:
    """
    Calculate stop loss based on ATR and market structure.
    
    Args:
        df: DataFrame with indicators and price data
        signal_type: "BUY" or "SELL"
        entry_price: Entry price for the trade
        
    Returns:
        Stop loss price
    """
    latest = df.iloc[-1]
    atr = latest['atr']
    
    if pd.isna(atr):
        # Fallback: use 2% of entry price
        atr_stop = entry_price * 0.02
    else:
        # Use ATR multiplier from config
        atr_stop = atr * config.ATR_MULTIPLIER
    
    if signal_type == "BUY":
        # Stop loss below entry
        # Look for recent swing low
        recent_lows = df.tail(config.SWING_LOOKBACK)['low'].min()
        structure_stop = recent_lows
        
        # Use the wider stop (more conservative)
        stop_loss = min(entry_price - atr_stop, structure_stop)
    else:  # SELL
        # Stop loss above entry
        # Look for recent swing high
        recent_highs = df.tail(config.SWING_LOOKBACK)['high'].max()
        structure_stop = recent_highs
        
        # Use the wider stop (more conservative)
        stop_loss = max(entry_price + atr_stop, structure_stop)
    
    return stop_loss


def validate_data_quality(df: pd.DataFrame) -> bool:
    """
    Validate that dataframe has sufficient quality data for analysis.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if data quality is acceptable
    """
    if df is None or len(df) < config.MIN_CANDLES_FOR_ANALYSIS:
        return False
    
    # Check for required columns
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    if not all(col in df.columns for col in required_columns):
        return False
    
    # Check for excessive NaN values in recent data
    recent_data = df.tail(50)
    if recent_data[required_columns].isna().sum().sum() > 5:
        return False
    
    return True
