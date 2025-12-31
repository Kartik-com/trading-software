import asyncio
import config
from scanner import scanner
import indicators
import smc
import pandas as pd

async def main():
    print("--- RESET LOGIC DIAGNOSTIC ---")
    symbol = "BTC/USDT"
    print(f"Checking {symbol}...")
    
    # 1. Fetch Data
    df15 = await scanner.fetch_ohlcv(symbol, config.ENTRY_TIMEFRAME)
    if df15 is None:
        print("ERROR: Could not fetch data.")
        return

    df15 = indicators.add_all_indicators(df15)
    
    # 2. Select Candle (Closed)
    # scanner logic:
    last_row = df15.iloc[-1]
    last_15 = df15.iloc[-2] # Assuming live fetch includes open candle
    # Let's verify timestamp
    print(f"Latest Fetched Timestamp: {last_row['timestamp']}")
    print(f"Using 'Closed' Candle Timestamp: {last_15['timestamp']}")
    
    # 3. Structure
    # scanner logic:
    # df15_slice = df15.iloc[:-1] # slice up to last_15
    # actually logic was complex slice. let's just use full DF up to -1
    df_slice = df15.iloc[:-1] 
    struct = smc.detect_structure(df_slice)
    print(f"Structure Detected: {struct}")
    
    # 4. EMA Alignment
    ema_periods = [20, 50, 100, 200]
    close_price = last_15['close']
    
    ema_vals = {p: last_15[f'ema_{p}'] for p in ema_periods}
    print(f"Close Price: {close_price}")
    print(f"EMAs: {ema_vals}")
    
    ema_bull = all(close_price > v for v in ema_vals.values())
    ema_bear = all(close_price < v for v in ema_vals.values())
    
    print(f"EMA Bull Aligned: {ema_bull}")
    print(f"EMA Bear Aligned: {ema_bear}")
    
    # 5. Stoch RSI
    stoch_k = last_15['stoch_rsi_k']
    print(f"Stoch RSI K: {stoch_k}")
    
    # 6. Conclusion
    print("\n--- DECISION ---")
    if struct in ["BOS_BULL", "CHoCH_BULL"]:
        if ema_bull:
            if stoch_k < 80.0:
                print(f">> MATCH: BUY SIGNAL should fire! (Stoch {stoch_k:.2f} < 80)")
            else:
                print(f">> NO SIGNAl: Stoch RSI {stoch_k:.2f} is >= 80 (Overbought).")
        else:
             print(">> NO SIGNAL: Price not above all EMAs.")
    elif struct in ["BOS_BEAR", "CHoCH_BEAR"]:
         if ema_bear:
            if stoch_k > 20.0:
                 print(f">> MATCH: SELL SIGNAL should fire! (Stoch {stoch_k:.2f} > 20)")
            else:
                 print(f">> NO SIGNAL: Stoch RSI {stoch_k:.2f} is <= 20 (Oversold).")
         else:
             print(">> NO SIGNAL: Price not below all EMAs.")
    else:
        print(">> NO SIGNAL: No valid Bull/Bear Structure pattern found.")

if __name__ == "__main__":
    asyncio.run(main())
