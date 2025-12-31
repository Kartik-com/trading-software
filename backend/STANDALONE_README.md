# Standalone Bot - Quick Start

This is a simplified version that works WITHOUT FastAPI or the full backend setup.

## Requirements

```bash
pip install ccxt pandas numpy requests ta
```

## Run

```bash
python standalone_bot.py
```

## What It Does

- Monitors BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT, XRP/USDT
- Scans every 15 minutes on candle close
- Sends Telegram alerts when signals are found
- Uses your configured Telegram bot

## Configuration

Edit `standalone_bot.py` to change:
- `SYMBOLS` - Trading pairs to monitor
- `BOT_TOKEN` - Your Telegram bot token
- `CHAT_ID` - Your Telegram chat ID

## Stopping

Press `Ctrl+C` to stop the bot gracefully.

---

**This is the simplest way to get started!** Once you have Python installed, just run this script.
