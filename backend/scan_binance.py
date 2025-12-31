import asyncio
import ccxt
import pandas as pd
import indicators
import smc
import config

async def check_all_binance():
    exchange = ccxt.binance()
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]
    print(f"--- BINANCE SCAN ({len(symbols)} symbols) ---")
    
    for symbol in symbols:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, "15m", limit=30)
            df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['ts'], unit='ms')
            df = indicators.add_all_indicators(df)
            
            struct = smc.detect_structure(df)
            
            # EMA match
            close = df.iloc[-1]['close']
            ema200 = df.iloc[-1]['ema_200']
            stoch = df.iloc[-1]['stoch_rsi_k']
            
            print(f"{symbol}: Struct={struct}, Close={close:.2f}, EMA200={ema200:.2f}, Stoch={stoch:.2f}")
            
            if struct:
                print(f"  !! POTENTIAL SIGNAL ON {symbol} !!")
        except Exception as e:
            print(f"{symbol}: Error {e}")

if __name__ == "__main__":
    asyncio.run(check_all_binance())
