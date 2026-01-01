
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
import config
from scanner import scanner
from models import Signal

# Mock Data Generation
def generate_perfect_buy_data():
    """Generates data that SHOULD trigger a strict BUY signal"""
    # 1. Generate 1H Data (Bullish Bias)
    # Price > EMA200
    dates_1h = pd.date_range(end=datetime.utcnow(), periods=200, freq='1h')
    df_1h = pd.DataFrame({
        'timestamp': dates_1h,
        'open': 100.0, 'high': 105.0, 'low': 95.0, 'close': 102.0, 'volume': 1000
    })
    # Make a steady uptrend so EMA200 is below price
    df_1h['close'] = np.linspace(100, 200, 200) 
    df_1h['high'] = df_1h['close'] + 2
    df_1h['low'] = df_1h['close'] - 2
    
    # 2. Generate 15m Data (Bullish Entry)
    dates_15m = pd.date_range(end=datetime.utcnow(), periods=200, freq='15min')
    df_15m = pd.DataFrame({
        'timestamp': dates_15m,
        'open': 100.0, 'high': 105.0, 'low': 95.0, 'close': 100.0, 'volume': 1000
    })
    
    # Base Uptrend
    df_15m['close'] = np.linspace(200, 210, 200)
    df_15m['high'] = df_15m['close'] + 2
    df_15m['low'] = df_15m['close'] - 2
    
    # Create EARLIER Swing High at index 100
    df_15m.loc[100, 'high'] = 215.0
    df_15m.loc[100, 'close'] = 214.0
    # Surroundings for 100
    for i in range(1, 6):
        df_15m.loc[100-i, 'high'] = 214.0 - i*0.1
        df_15m.loc[100+i, 'high'] = 214.0 - i*0.1

    # Create Swing High at index 150 (Need lookback=5 candles on both sides)
    # 145-155: 150 is Highest
    mid_idx = 150
    df_15m.loc[mid_idx, 'high'] = 220.0
    df_15m.loc[mid_idx, 'close'] = 219.0
    
    # Ensure surrounding candles are lower
    for i in range(1, 6):
        df_15m.loc[mid_idx-i, 'high'] = 218.0 - i*0.1
        df_15m.loc[mid_idx+i, 'high'] = 218.0 - i*0.1
        
    # Price dips after 150, then rallies
    # From 160 to 198, price climbs back
    # At 199 (Last), Price breaks 220
    df_15m.loc[198, 'close'] = 219.5
    df_15m.loc[198, 'high'] = 219.8
    
    df_15m.loc[199, 'close'] = 221.0 # BREAK!
    df_15m.loc[199, 'high'] = 222.0
    
    # Ensure EMAs are aligned at the end
    # We'll just force the columns to be aligned for the test logic "calculate_signal_score" uses
    # But wait, scanner calls "indicators.add_all_indicators(df_15m)" which RECALCULATES them from close price.
    # So my close price MUST result in valid EMAs.
    # A steady climb from 210 to 221 over 50 candles should work.
    
    # Let's fix the close prices from 160 to 199 to be a steady strong uptrend
    # ensuring Price > EMA20 > EMA50
    start_val = 215.0
    end_val = 221.0
    ramp = np.linspace(start_val, end_val, 40)
    df_15m.iloc[160:200, df_15m.columns.get_loc('close')] = ramp
    
    return df_1h, df_15m

async def run_test():
    print("--- Starting Verification ---")
    
    # Mock methods to return our perfect data
    original_fetch = scanner.fetch_ohlcv
    
    df_1h, df_15m = generate_perfect_buy_data()
    
    async def mock_fetch(symbol, timeframe, limit=None):
        if timeframe == config.BIAS_TIMEFRAME:
            return df_1h
        return df_15m
        
    scanner.fetch_ohlcv = mock_fetch
    
    # Run evaluation
    symbol = "BTC/TEST"
    print(f"Evaluating {symbol} with Mock Data...")
    
    # Run evaluation
    symbol = "BTC/TEST"
    print(f"Evaluating {symbol} with Mock Data...")
    
    # DEBUG: Check SMC directly
    import smc
    struct = smc.detect_structure(df_15m)
    print(f"DEBUG SMC Structure: {struct}")
    
    signal = await scanner.evaluate_symbol(symbol, config.ENTRY_TIMEFRAME)
    
    if signal:
        print("\n✅ SIGNAL GENERATED!")
        print(f"Type: {signal.signal_type}")
        print(f"Confidence: {signal.confidence}")
        print(f"Bias: {signal.bias}")
        print(f"Structure: {signal.structure}")
        print(f"RSI: {signal.rsi}")
        print(f"EMA Aligned: {signal.ema_alignment}")
        
        if signal.confidence == "HIGH":
             print("\n🏆 SUCCESS: High Confidence Signal Validated")
        else:
             print("\n⚠️ WARNING: Signal generated but not HIGH confidence")
    else:
        print("\n❌ NO SIGNAL GENERATED")
        
    # Validation of Negative Test (Bearish Bias but Bullish Signal -> Should Fail)
    print("\n--- Negative Test (Conflicting Bias) ---")
    # Invert 1h to be bearish
    df_1h_bear = df_1h.copy()
    df_1h_bear['close'] = np.linspace(200, 100, 200) # Downtrend
    
    async def mock_fetch_bear(symbol, timeframe, limit=None):
        if timeframe == config.BIAS_TIMEFRAME:
             return df_1h_bear
        return df_15m # Still Bullish Setup
        
    scanner.fetch_ohlcv = mock_fetch_bear
    signal_fail = await scanner.evaluate_symbol(symbol, config.ENTRY_TIMEFRAME)
    
    if signal_fail is None:
        print("✅ SUCCESS: Conflicting signal correctly filtered out")
    else:
        print(f"❌ FAILURE: Should not have generated signal! Got: {signal_fail.signal_type}")

if __name__ == "__main__":
    asyncio.run(run_test())
