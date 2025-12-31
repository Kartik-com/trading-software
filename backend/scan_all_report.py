import asyncio
import config
from scanner import scanner
import indicators
import smc
import pandas as pd

async def main():
    print("--- FULL MARKET STATUS REPORT (15m) ---")
    symbols = config.SYMBOLS
    
    for symbol in symbols:
        print(f"\nChecking {symbol}...")
        df = await scanner.fetch_ohlcv(symbol, "15m", limit=30)
        if df is None:
            print(f"  - ERROR: Could not fetch data for {symbol}")
            continue
            
        df = indicators.add_all_indicators(df)
        last_row = df.iloc[-1]
        last_closed = df.iloc[-2]
        
        # 1. Structure
        struct = smc.detect_structure(df.iloc[:-1])
        
        # 2. EMAs
        ema_periods = [20, 50, 100, 200]
        close = last_closed['close']
        ema_bull = all(close > last_closed[f'ema_{p}'] for p in ema_periods if f'ema_{p}' in last_closed)
        ema_bear = all(close < last_closed[f'ema_{p}'] for p in ema_periods if f'ema_{p}' in last_closed)
        
        # 3. Stoch
        stoch = last_closed['stoch_rsi_k']
        
        print(f"  - Structure: {struct if struct else 'NONE'}")
        print(f"  - EMA Bull: {'PASS' if ema_bull else 'FAIL'}")
        print(f"  - EMA Bear: {'PASS' if ema_bear else 'FAIL'}")
        print(f"  - StochRSI: {stoch:.2f} (Buy requires < 80, Sell > 20)")
        
        # Decision
        if struct in ["BOS_BULL", "CHoCH_BULL"] and ema_bull and stoch < 80:
            print(f"  !! SHOULD HAVE SIGNAL !!")
        elif struct in ["BOS_BEAR", "CHoCH_BEAR"] and ema_bear and stoch > 20:
             print(f"  !! SHOULD HAVE SIGNAL !!")
        else:
            reasons = []
            if not struct: reasons.append("No HH+HL or LL+LH")
            if not (ema_bull or ema_bear): reasons.append("Price not clearing all EMAs")
            if (struct in ["BOS_BULL", "CHoCH_BULL"]) and stoch >= 80: reasons.append("Stoch Overbought")
            if (struct in ["BOS_BEAR", "CHoCH_BEAR"]) and stoch <= 20: reasons.append("Stoch Oversold")
            print(f"  - Verdict: WAITING ({', '.join(reasons)})")

if __name__ == "__main__":
    asyncio.run(main())
