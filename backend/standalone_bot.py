"""
Standalone trading bot - simplified version that works without FastAPI.
Based on proven Colab implementation.
Run this directly: python standalone_bot.py
"""
import ccxt
import pandas as pd
import requests
import time
from datetime import datetime, timezone
from ta.momentum import StochRSIIndicator

# ================= CONFIG =================
import os
from dotenv import load_dotenv
load_dotenv()

EXCHANGE = ccxt.binance()  # Changed from Kraken to Binance
SYMBOLS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"]
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

ATR_PERIOD = 14
EMA_PERIODS = [20, 50, 100, 200]
ATR_MULTIPLIER = 1.5
# ==========================================

def send_telegram(msg):
    """Send message to Telegram"""
    if BOT_TOKEN and CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": msg},
                timeout=10
            )
            print(f"✅ Telegram alert sent")
        except Exception as e:
            print(f"❌ Telegram error: {e}")

def fetch(symbol, tf, limit=200):
    """Fetch OHLCV data from exchange"""
    try:
        ohlcv = EXCHANGE.fetch_ohlcv(symbol, tf, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","vol"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms")
        return df
    except Exception as e:
        print(f"❌ Error fetching {symbol} {tf}: {e}")
        return None

def indicators(df):
    """Add technical indicators"""
    # EMAs
    for p in EMA_PERIODS:
        df[f"ema{p}"] = df["close"].ewm(span=p, adjust=False).mean()
    
    # ATR
    df["atr"] = (df["high"]-df["low"]).rolling(ATR_PERIOD).mean()
    
    # Stochastic RSI
    try:
        stoch = StochRSIIndicator(df["close"], window=14)
        df["stoch"] = stoch.stochrsi()
    except:
        df["stoch"] = 0.5
    
    return df

def structure(df):
    """Detect market structure"""
    if len(df) < 2:
        return None
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # BOS: Break above previous high
    if last["high"] > prev["high"]:
        return "BOS"
    
    # CHoCH: Break below previous low
    if last["low"] < prev["low"]:
        return "CHoCH"
    
    return None

def bias_1h(df):
    """Determine 1H market bias"""
    if len(df) < 200:
        return "RANGE"
    
    last = df.iloc[-1]
    
    if last["close"] > last["ema200"]:
        return "BULLISH"
    elif last["close"] < last["ema200"]:
        return "BEARISH"
    else:
        return "RANGE"

def confidence(bias, struct, stoch):
    """Calculate signal confidence"""
    score = 0
    if bias != "RANGE": score += 1
    if struct: score += 1
    if stoch < 0.2 or stoch > 0.8: score += 1
    return ["LOW","MEDIUM","HIGH"][min(score,2)]

def evaluate(symbol):
    """Evaluate symbol for trading signals"""
    try:
        # Fetch data
        df1h = fetch(symbol, "1h", limit=200)
        df15 = fetch(symbol, "15m", limit=200)
        
        if df1h is None or df15 is None:
            return
        
        # Add indicators
        df1h = indicators(df1h)
        df15 = indicators(df15)
        
        # Get bias and structure
        bias = bias_1h(df1h)
        struct = structure(df15)
        
        if not struct:
            return
        
        last = df15.iloc[-1]
        
        # Determine signal direction
        direction = None
        sl = None
        
        # BUY signal: Bullish bias + BOS
        if bias == "BULLISH" and struct == "BOS":
            direction = "BUY"
            sl = last["close"] - last["atr"] * ATR_MULTIPLIER
        
        # SELL signal: Bearish bias + CHoCH
        elif bias == "BEARISH" and struct == "CHoCH":
            direction = "SELL"
            sl = last["close"] + last["atr"] * ATR_MULTIPLIER
        
        if not direction:
            return
        
        # Calculate confidence
        conf = confidence(bias, struct, last["stoch"])
        
        # Format message
        emoji = "🟢" if direction == "BUY" else "🔴"
        msg = (
            f"{emoji} {direction} SIGNAL — {symbol}\n"
            f"Timeframe: 15m\n"
            f"Bias (1H): {bias}\n"
            f"Structure: {struct} confirmed\n"
            f"Entry Price: {round(last['close'],2)}\n"
            f"Stop Loss: {round(sl,2)}\n"
            f"Confidence: {conf}\n"
            f"Candle Close: {last['ts'].strftime('%Y-%m-%d %H:%M UTC')}"
        )
        
        print(f"\n{msg}\n")
        send_telegram(msg)
        
    except Exception as e:
        print(f"❌ Error evaluating {symbol}: {e}")

# Main loop
print("🚀 Crypto Trading Bot Started")
print(f"📊 Monitoring: {', '.join(SYMBOLS)}")
print(f"⏰ Scanning every 15 minutes on candle close\n")

# Send startup message
send_telegram("🤖 Crypto Trading Bot Started\n\nMonitoring markets for signals...")

last_15m = None

while True:
    try:
        now = datetime.now(timezone.utc)
        
        # Check if 15m candle closed
        if now.minute % 15 == 0 and last_15m != now.minute:
            print(f"\n⏰ 15m candle closed at {now.strftime('%H:%M UTC')}")
            print("🔍 Scanning all symbols...")
            
            for s in SYMBOLS:
                evaluate(s)
            
            last_15m = now.minute
            print("✅ Scan complete\n")
        
        # Wait 60 seconds before next check
        time.sleep(60)
        
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")
        send_telegram("🛑 Crypto Trading Bot Stopped")
        break
    except Exception as e:
        print(f"❌ Error in main loop: {e}")
        time.sleep(60)
