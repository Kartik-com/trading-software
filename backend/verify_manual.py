import asyncio
import config
from scanner import scanner
import indicators

async def main():
    print("--- MANUAL MARKET VERIFICATION ---")
    symbol = "BTC/USDT"
    print(f"Checking {symbol}...")
    
    # 1. Fetch Data
    df1h = await scanner.fetch_ohlcv(symbol, config.BIAS_TIMEFRAME)
    df15 = await scanner.fetch_ohlcv(symbol, config.ENTRY_TIMEFRAME)
    
    if df1h is None or df15 is None:
        print("ERROR: Could not fetch data.")
        return

    df1h = indicators.add_all_indicators(df1h)
    df15 = indicators.add_all_indicators(df15)

    # 2. Check Bias
    last_1h = df1h.iloc[-1]
    bias = "RANGE"
    if last_1h["close"] > last_1h["ema_200"]:
        bias = "BULLISH"
    elif last_1h["close"] < last_1h["ema_200"]:
        bias = "BEARISH"
    
    print(f"1H Bias: {bias} (Close: {last_1h['close']} vs EMA200: {last_1h['ema_200']})")
    
    # 3. Check Structure
    import smc
    # We need to simulate the "High > Prev High" check exactly as scanner does
    # scanner uses get_closed_candle logic. Let's look at the raw tail.
    print("\nRecent 15m Candles:")
    print(df15.tail(3)[['timestamp', 'open', 'high', 'low', 'close']])
    
    # Check structure on full DF
    struct = smc.detect_structure(df15)
    print(f"\nStructure Detected (Latest): {struct}")
    
    # Check if mismatch
    print("\n--- CONCLUSION ---")
    if not struct:
        print("NO SIGNAL: No Break of Structure (High > PrevHigh or Low < PrevLow) on latest closed candle.")
    elif (bias == "BULLISH" and struct != "BOS"):
         print(f"NO SIGNAL: Bias is BULLISH but Structure is {struct} (Need BOS).")
    elif (bias == "BEARISH" and struct != "CHoCH"):
         print(f"NO SIGNAL: Bias is BEARISH but Structure is {struct} (Need CHoCH).")
    else:
        print("SIGNAL SHOULD FIRE! If you don't see it, there's a bug.")

if __name__ == "__main__":
    asyncio.run(main())
