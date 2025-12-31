
import asyncio
import os
import sys
import logging

# Ensure backend dir is in path
sys.path.append(os.getcwd())

import config
from scanner import scanner

# Configure logging to ensure we see output
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("scanner")
logger.setLevel(logging.INFO)

async def manual_scan():
    print(f"--- STARTING MANUAL SCAN ({config.ENTRY_TIMEFRAME}) ---")
    print(f"Lookback: {config.SWING_LOOKBACK}")
    
    signals = await scanner.scan_all_symbols(config.ENTRY_TIMEFRAME)
    
    print(f"--- SCAN COMPLETE ---")
    print(f"Signals Found: {len(signals)}")
    for s in signals:
        print(f"SIGNAL: {s.symbol} {s.signal_type} {s.confidence}")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(manual_scan())
    except Exception as e:
        print(f"Error: {e}")
