# Crypto Trading Analysis System

A production-ready real-time cryptocurrency market analysis platform that monitors crypto markets, analyzes price action using Smart Money Concepts, and generates BUY/SELL/REVERSAL signals with multi-timeframe confirmation.

## ⚠️ Disclaimer

**This system is for educational and informational purposes only.** Cryptocurrency trading carries significant risk. This is NOT financial advice. Always do your own research and never risk more than you can afford to lose. The system does NOT execute trades automatically - all signals are for manual execution only.

## Features

- 📊 **Real-time Market Analysis** - Monitors multiple cryptocurrency pairs continuously
- 🧠 **Smart Money Concepts** - Detects market structure, BOS, CHoCH, and liquidity sweeps
- 📈 **Technical Indicators** - EMAs (20, 50, 100, 200) and Stochastic RSI
- ⏰ **Multi-Timeframe Confirmation** - 1H bias with 15m entry signals
- 📱 **Telegram Alerts** - Instant notifications with detailed signal information
- 💻 **Modern Dashboard** - Real-time web interface with charts and signal feed
- 🎯 **Confidence Scoring** - HIGH/MEDIUM/LOW confidence based on signal alignment

## System Architecture

### Backend (Python + FastAPI)
- **FastAPI** - High-performance async API
- **CCXT** - Exchange connectivity (Binance default)
- **Pandas/NumPy** - Technical analysis calculations
- **Python-Telegram-Bot** - Alert delivery
- **WebSockets** - Real-time updates

### Frontend (Next.js + TypeScript)
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **TradingView Lightweight Charts** - Professional charting
- **Axios** - API communication

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Telegram Bot Token (from @BotFather)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your Telegram credentials:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

5. Run the backend:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

4. Run the development server:
```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

## Configuration

### Trading Pairs

Edit `backend/config.py` to modify monitored symbols:

```python
SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
]
```

### Indicator Parameters

Adjust indicator settings in `backend/config.py`:

```python
EMA_PERIODS = [20, 50, 100, 200]
STOCH_RSI_PERIOD = 14
ATR_PERIOD = 14
```

### Exchange

To use a different exchange, modify `backend/config.py`:

```python
EXCHANGE = "binance"  # or "coinbase", "kraken", etc.
```

## Getting Telegram Credentials

1. **Create a Bot**:
   - Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Copy the bot token

2. **Get Chat ID**:
   - Start a chat with your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response

## Signal Format

Signals are sent in this format:

```
🟢 BUY SIGNAL — BTC/USDT
Timeframe: 15m
Bias (1H): BULLISH
Structure: BOS confirmed
Entry Price: 42350.5
Stop Loss: 42190.2
Confidence: HIGH
Candle Close: 2025-01-12 11:15 UTC
```

## API Endpoints

- `GET /api/symbols` - List monitored symbols
- `GET /api/signals` - Get recent signals
- `GET /api/bias/{symbol}` - Get market bias for symbol
- `GET /api/price/{symbol}` - Get current price data
- `WebSocket /ws/signals` - Real-time signal stream

## Deployment

### Backend Deployment (Railway/Render)

1. Create a new project
2. Connect your repository
3. Set environment variables
4. Deploy

### Frontend Deployment (Vercel)

1. Import your repository to Vercel
2. Set `NEXT_PUBLIC_API_URL` to your backend URL
3. Deploy

## How It Works

1. **Market Scanning**: Every candle close (15m, 1h), the system fetches OHLCV data
2. **Indicator Calculation**: Computes EMAs, Stochastic RSI, and ATR
3. **SMC Analysis**: Detects market structure, BOS, CHoCH, and liquidity sweeps
4. **Signal Generation**: Evaluates conditions for BUY/SELL/REVERSAL signals
5. **Multi-Timeframe Confirmation**: Ensures 1h bias aligns with 15m entry
6. **Alert Distribution**: Sends formatted alerts via Telegram and WebSocket

## Signal Logic

### BUY Signal
- 1H bias: BULLISH
- 15m: BOS confirmed (break above previous high)
- Price near EMA 20/50
- Stochastic RSI oversold recovery
- Confidence: HIGH if all align

### SELL Signal
- 1H bias: BEARISH
- 15m: BOS confirmed (break below previous low)
- Price near EMA 20/50
- Stochastic RSI overbought decline
- Confidence: HIGH if all align

### REVERSAL Signal
- CHoCH detected (market structure shift)
- Liquidity sweep confirmed
- Confidence: MEDIUM (reversals are riskier)

## Troubleshooting

### Backend Issues

**No data fetching:**
- Check internet connection
- Verify exchange is accessible
- Check CCXT version compatibility

**No Telegram alerts:**
- Verify bot token and chat ID
- Ensure bot is not blocked
- Check Telegram API status

### Frontend Issues

**Chart not loading:**
- Verify backend is running
- Check API URL in `.env.local`
- Check browser console for errors

**WebSocket not connecting:**
- Ensure backend WebSocket endpoint is accessible
- Check CORS settings in backend

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.

---

**Remember**: This is a trading analysis tool, not a trading bot. All signals require manual review and execution. Trade responsibly!
