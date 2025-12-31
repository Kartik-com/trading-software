# Quick Start Guide

## Prerequisites
- Python 3.10+ installed (**[See PYTHON_SETUP.md if not installed](PYTHON_SETUP.md)**)
- Node.js 18+ installed
- Telegram account

## Step 0: Install Python (If Needed)

**Check if Python is installed:**
```bash
python --version
```

If you see "Python was not found", follow **[PYTHON_SETUP.md](PYTHON_SETUP.md)** first, then come back here.

## Step 1: Get Telegram Credentials

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Copy the **bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. Start a chat with your bot
5. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
6. Find your **chat ID** in the response (looks like: `123456789`)

## Step 2: Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your credentials
# TELEGRAM_BOT_TOKEN=your_token_here
# TELEGRAM_CHAT_ID=your_chat_id_here

# Run the backend
python main.py
```

Backend will be running at: **http://localhost:8000**

## Step 3: Frontend Setup

Open a **new terminal**:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run the frontend
npm run dev
```

Dashboard will be available at: **http://localhost:3000**

## Step 4: Verify It's Working

1. Check backend terminal - you should see:
   - "Trading analysis system started"
   - "Telegram alert service initialized"
   - "Candle close scheduler started"

2. Check Telegram - you should receive a test message

3. Open http://localhost:3000 in your browser
   - Dashboard should load
   - Status should show "Live"
   - Select a symbol from dropdown

4. Wait for signals (may take time depending on market conditions)

## Troubleshooting

### Backend Issues

**"Telegram not configured"**
- Check your `.env` file has correct bot token and chat ID
- Ensure no extra spaces or quotes

**"Failed to fetch market data"**
- Check internet connection
- Binance might be rate limiting - wait a few minutes

### Frontend Issues

**"Failed to connect to backend"**
- Ensure backend is running on port 8000
- Check `.env.local` has correct API URL

**WebSocket not connecting**
- Refresh the page
- Check backend logs for errors

## What to Expect

- **Candle Close Timing**: System scans every 15 minutes and every hour
- **First Signal**: May take time depending on market conditions
- **Telegram Alerts**: Sent instantly when signals are generated
- **Dashboard Updates**: Real-time via WebSocket

## Next Steps

1. Monitor the dashboard for signals
2. Review signals in Telegram
3. Manually execute trades if you choose
4. Adjust configuration in `backend/config.py` as needed

## Important Reminders

⚠️ **This is NOT an auto-trading bot** - all signals are for manual execution
⚠️ **Trade at your own risk** - cryptocurrency trading is highly risky
⚠️ **Do your own research** - don't blindly follow signals

---

For detailed documentation, see [README.md](README.md)
