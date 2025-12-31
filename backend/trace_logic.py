import asyncio
import config
from scanner import scanner
import indicators
import smc
import pandas as pd

async def main():
    print("--- DEEP TRACE BTC/USD ---")
    symbol = "BTC/USD"
    
    # 1. Fetch Data
    df = await scanner.fetch_ohlcv(symbol, "15m", limit=10)
    if df is None: return

    # 2. Add indicators
    df = indicators.add_all_indicators(df)
    
    # 3. Last 3 candles
    print("\nLast 3 Candles (Closed):")
    for i in range(-3, 0):
        row = df.iloc[i]
        print(f"TS: {row['timestamp']} | H: {row['high']:.2f} | L: {row['low']:.2f} | C: {row['close']:.2f}")

    # 4. Check BOS_BULL condition
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    h_break = last["high"] > prev["high"]
    l_break = last["low"] > prev["low"]
    
    print(f"\nCondition: last['high'] > prev['high'] -> {h_break} ({last['high']:.2f} > {prev['high']:.2f})")
    print(f"Condition: last['low'] > prev['low'] -> {l_break} ({last['low']:.2f} > {prev['low']:.2f})")
    
    if h_break and l_break:
        print(">> BOS_BULL DETECTED!")
    else:
        print(">> NO BOS_BULL.")

if __name__ == "__main__":
    asyncio.run(main())
