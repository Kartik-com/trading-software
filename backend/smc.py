"""
Smart Money Concepts (SMC) implementation.
Detects market structure, BOS, CHoCH, and liquidity sweeps algorithmically.
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict
from models import MarketStructure
from datetime import datetime
import config


def find_swing_highs_lows(df: pd.DataFrame, lookback: int = None) -> Tuple[pd.Series, pd.Series]:
    """
    Identify swing highs and swing lows using pivot detection.
    
    Args:
        df: DataFrame with OHLCV data
        lookback: Number of candles to look back (default from config)
        
    Returns:
        Tuple of (swing_highs Series, swing_lows Series) with NaN for non-swing points
    """
    lookback = lookback or config.SWING_LOOKBACK
    
    swing_highs = pd.Series(index=df.index, dtype=float)
    swing_lows = pd.Series(index=df.index, dtype=float)
    
    for i in range(lookback, len(df) - lookback):
        # Check if current high is highest in the window
        window_highs = df['high'].iloc[i - lookback:i + lookback + 1]
        if df['high'].iloc[i] == window_highs.max():
            swing_highs.iloc[i] = df['high'].iloc[i]
        
        # Check if current low is lowest in the window
        window_lows = df['low'].iloc[i - lookback:i + lookback + 1]
        if df['low'].iloc[i] == window_lows.min():
            swing_lows.iloc[i] = df['low'].iloc[i]
    
    return swing_highs, swing_lows


def detect_market_structure(df: pd.DataFrame) -> List[MarketStructure]:
    """
    Detect market structure changes (HH, HL, LH, LL).
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        List of MarketStructure objects
    """
    swing_highs, swing_lows = find_swing_highs_lows(df)
    
    structures = []
    
    # Get valid swing points
    valid_highs = swing_highs.dropna()
    valid_lows = swing_lows.dropna()
    
    # Track previous swing high and low
    prev_high = None
    prev_low = None
    
    # Analyze swing highs
    for idx, high in valid_highs.items():
        if prev_high is not None:
            if high > prev_high:
                # Higher High
                structures.append(MarketStructure(
                    type="HH",
                    price=high,
                    timestamp=df.loc[idx, 'timestamp']
                ))
            else:
                # Lower High
                structures.append(MarketStructure(
                    type="LH",
                    price=high,
                    timestamp=df.loc[idx, 'timestamp']
                ))
        prev_high = high
    
    # Analyze swing lows
    for idx, low in valid_lows.items():
        if prev_low is not None:
            if low > prev_low:
                # Higher Low
                structures.append(MarketStructure(
                    type="HL",
                    price=low,
                    timestamp=df.loc[idx, 'timestamp']
                ))
            else:
                # Lower Low
                structures.append(MarketStructure(
                    type="LL",
                    price=low,
                    timestamp=df.loc[idx, 'timestamp']
                ))
        prev_low = low
    
    # Sort by timestamp
    structures.sort(key=lambda x: x.timestamp)
    
    return structures


def detect_structure(df: pd.DataFrame) -> Optional[str]:
    """
    Simplified Structure Detection matching User's 'Reset' Logic.
    
    Rules:
    - BOS_BULL: Last High > Prev High AND Last Low > Prev Low
    - BOS_BEAR: Last Low < Prev Low AND Last High < Prev High
    - CHoCH_BULL: Last Low < Prev Low AND Last Close > Prev Open (Engulfing/rejection?)
      Wait, user script says: last["close"] > prev["open"]. 
      Note: prev["open"] is the open of the PREVIOUS candle.
    - CHoCH_BEAR: Last High > Prev High AND Last Close < Prev Open
    """
    if len(df) < 2:
        return None
        
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # BOS_BULL (Strong uptrend continuation)
    if last["high"] > prev["high"] and last["low"] > prev["low"]:
        return "BOS_BULL"
        
    # BOS_BEAR (Strong downtrend continuation)
    if last["low"] < prev["low"] and last["high"] < prev["high"]:
        return "BOS_BEAR"
        
    # CHoCH_BULL (Reversal Up?)
    # "last low < prev low" (sweep) AND "last close > prev open" (strong close)
    if last["low"] < prev["low"] and last["close"] > prev["open"]:
        return "CHoCH_BULL"
        
    # CHoCH_BEAR (Reversal Down?)
    # "last high > prev high" (sweep) AND "last close < prev open" (strong drop)
    if last["high"] > prev["high"] and last["close"] < prev["open"]:
        return "CHoCH_BEAR"
        
    return None

# Deprecating old complex functions but keeping them as stubs if needed or removing them.
# For this task, we will just use the new `detect_structure` in the scanner.


def determine_structure_bias(structures: List[MarketStructure]) -> str:
    """
    Determine market bias based solely on recent structure.
    
    Rules:
    - Series of HH + HL = BULLISH
    - Series of LH + LL = BEARISH
    
    Args:
        structures: List of MarketStructure objects
        
    Returns:
        "BULLISH", "BEARISH", or "NEUTRAL"
    """
    if not structures:
        return "NEUTRAL"
        
    # Look at the last few structure points
    recent = structures[-3:]
    
    # Count bullish vs bearish points
    bullish_pts = sum(1 for s in recent if s.type in ["HH", "HL"])
    bearish_pts = sum(1 for s in recent if s.type in ["LH", "LL"])
    
    if bullish_pts > bearish_pts:
        return "BULLISH"
    elif bearish_pts > bullish_pts:
        return "BEARISH"
    
    # If mixed or equal (rare in 3 points), look at the very last one
    last_type = structures[-1].type
    if last_type in ["HH", "HL"]:
        return "BULLISH"
    elif last_type in ["LH", "LL"]:
        return "BEARISH"
        
    return "NEUTRAL"


def detect_liquidity_sweep(df: pd.DataFrame, tolerance: float = None) -> Optional[Dict]:
    """
    Detect liquidity sweeps (equal highs/lows that get taken out).
    
    Args:
        df: DataFrame with OHLCV data
        tolerance: Price tolerance for "equal" levels (default from config)
        
    Returns:
        Dict with sweep info or None
    """
    tolerance = tolerance or config.LIQUIDITY_TOLERANCE
    
    if len(df) < 10:
        return None
    
    recent = df.tail(10)
    latest = df.iloc[-1]
    
    # Find equal highs (within tolerance)
    highs = recent['high'].values
    for i in range(len(highs) - 2):
        for j in range(i + 1, len(highs) - 1):
            # Check if two highs are approximately equal
            if abs(highs[i] - highs[j]) / highs[i] < tolerance:
                equal_high = max(highs[i], highs[j])
                # Check if latest candle swept above and closed below
                if latest['high'] > equal_high and latest['close'] < equal_high:
                    return {
                        "type": "BULLISH_SWEEP",  # Sweep above, likely reversal down
                        "level": equal_high,
                        "timestamp": latest['timestamp']
                    }
    
    # Find equal lows (within tolerance)
    lows = recent['low'].values
    for i in range(len(lows) - 2):
        for j in range(i + 1, len(lows) - 1):
            # Check if two lows are approximately equal
            if abs(lows[i] - lows[j]) / lows[i] < tolerance:
                equal_low = min(lows[i], lows[j])
                # Check if latest candle swept below and closed above
                if latest['low'] < equal_low and latest['close'] > equal_low:
                    return {
                        "type": "BEARISH_SWEEP",  # Sweep below, likely reversal up
                        "level": equal_low,
                        "timestamp": latest['timestamp']
                    }
    
    return None


def analyze_smc(df: pd.DataFrame) -> Dict:
    """
    Perform complete SMC analysis on the dataframe.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Dict containing all SMC analysis results
    """
    # Detect market structure
    structures = detect_market_structure(df)
    
    # Detect BOS
    bos = detect_bos(df, structures)
    
    # Detect CHoCH
    choch = detect_choch(df, structures)
    
    # Detect liquidity sweeps
    sweep = detect_liquidity_sweep(df)
    
    # Determine Structural Bias
    bias = determine_structure_bias(structures)
    
    return {
        "structures": structures,
        "bos": bos,
        "choch": choch,
        "liquidity_sweep": sweep,
        "structure_bias": bias
    }


def get_structure_description(smc_analysis: Dict) -> str:
    """
    Get human-readable description of current market structure.
    
    Args:
        smc_analysis: Result from analyze_smc()
        
    Returns:
        String description
    """
    descriptions = []
    
    if smc_analysis.get("bos"):
        bos_type = smc_analysis["bos"]["type"]
        descriptions.append(f"BOS: {bos_type}")

    if smc_analysis.get("choch"):
        choch_type = smc_analysis["choch"]["type"]
        descriptions.append(f"CHoCH: {choch_type}")
    
    if smc_analysis.get("liquidity_sweep"):
        sweep_type = smc_analysis["liquidity_sweep"]["type"]
        descriptions.append(f"Sweep: {sweep_type}")
        
    bias = smc_analysis.get("structure_bias", "NEUTRAL")
    descriptions.append(f"Structure Bias: {bias}")
    
    return " | ".join(descriptions)
