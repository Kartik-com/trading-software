"""
Timeframe synchronization and candle close timing logic.
Ensures alerts are only sent on candle close, never mid-candle.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Callable, List
import logging
import config

logger = logging.getLogger(__name__)


class CandleCloseScheduler:
    """
    Manages candle close detection and triggers analysis at the right time.
    """
    
    def __init__(self):
        self.callbacks: Dict[str, List[Callable]] = {
            "5m": [],
            "15m": [],
            "1h": []
        }
        self.running = False
        
    def register_callback(self, timeframe: str, callback: Callable):
        """
        Register a callback to be called when a candle closes.
        
        Args:
            timeframe: Timeframe to monitor ("5m", "15m", "1h")
            callback: Async function to call on candle close
        """
        if timeframe in self.callbacks:
            self.callbacks[timeframe].append(callback)
            logger.info(f"Registered callback for {timeframe} candle closes")
        else:
            logger.warning(f"Unknown timeframe: {timeframe}")
    
    def get_next_candle_close(self, timeframe: str) -> datetime:
        """
        Calculate the next candle close time for a given timeframe.
        
        Args:
            timeframe: Timeframe ("5m", "15m", "1h")
            
        Returns:
            DateTime of next candle close (UTC)
        """
        now = datetime.utcnow()
        
        if timeframe == "5m":
            minutes = 5
        elif timeframe == "15m":
            minutes = 15
        elif timeframe == "1h":
            minutes = 60
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        # Calculate minutes since midnight
        minutes_since_midnight = now.hour * 60 + now.minute
        
        # Find next interval
        next_interval = ((minutes_since_midnight // minutes) + 1) * minutes
        
        # Calculate next close time
        next_close = now.replace(second=0, microsecond=0)
        next_close = next_close.replace(
            hour=next_interval // 60,
            minute=next_interval % 60
        )
        
        # If we've gone past midnight, add a day
        if next_close <= now:
            next_close += timedelta(days=1)
        
        return next_close
    
    def is_candle_closed(self, timeframe: str, last_check: datetime) -> bool:
        """
        Check if a candle has closed since the last check.
        
        Args:
            timeframe: Timeframe to check
            last_check: Last time we checked
            
        Returns:
            True if candle has closed
        """
        now = datetime.utcnow()
        
        if timeframe == "5m":
            minutes = 5
        elif timeframe == "15m":
            minutes = 15
        elif timeframe == "1h":
            minutes = 60
        else:
            return False
        
        # Get current and last interval
        current_interval = (now.hour * 60 + now.minute) // minutes
        last_interval = (last_check.hour * 60 + last_check.minute) // minutes
        
        # Also check if day changed
        day_changed = now.day != last_check.day
        
        return current_interval != last_interval or day_changed
    
    async def run(self):
        """
        Main loop that checks for candle closes and triggers callbacks.
        Runs every 10 seconds to detect closes promptly.
        """
        self.running = True
        last_checks = {tf: datetime.utcnow() for tf in self.callbacks.keys()}
        
        logger.info("Candle close scheduler started")
        
        while self.running:
            try:
                now = datetime.utcnow()
                
                # Check each timeframe
                for timeframe in self.callbacks.keys():
                    if self.is_candle_closed(timeframe, last_checks[timeframe]):
                        logger.info(f"{timeframe} candle closed at {now.isoformat()}")
                        
                        # Trigger all callbacks for this timeframe
                        for callback in self.callbacks[timeframe]:
                            try:
                                await callback(timeframe, now)
                            except Exception as e:
                                logger.error(f"Error in {timeframe} callback: {e}", exc_info=True)
                        
                        # Update last check time
                        last_checks[timeframe] = now
                
                # Wait 10 seconds before next check
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(10)
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        logger.info("Candle close scheduler stopped")


def timeframe_to_minutes(timeframe: str) -> int:
    """
    Convert timeframe string to minutes.
    
    Args:
        timeframe: Timeframe string ("5m", "15m", "1h", etc.)
        
    Returns:
        Number of minutes
    """
    if timeframe.endswith('m'):
        return int(timeframe[:-1])
    elif timeframe.endswith('h'):
        return int(timeframe[:-1]) * 60
    elif timeframe.endswith('d'):
        return int(timeframe[:-1]) * 1440
    else:
        raise ValueError(f"Unknown timeframe format: {timeframe}")


def align_timestamp_to_candle(timestamp: datetime, timeframe: str) -> datetime:
    """
    Align a timestamp to the start of its candle.
    
    Args:
        timestamp: Timestamp to align
        timeframe: Timeframe to align to
        
    Returns:
        Aligned timestamp (start of candle)
    """
    minutes = timeframe_to_minutes(timeframe)
    
    # Calculate minutes since midnight
    minutes_since_midnight = timestamp.hour * 60 + timestamp.minute
    
    # Find current interval start
    interval_start = (minutes_since_midnight // minutes) * minutes
    
    # Create aligned timestamp
    aligned = timestamp.replace(second=0, microsecond=0)
    aligned = aligned.replace(
        hour=interval_start // 60,
        minute=interval_start % 60
    )
    
    return aligned


# Global scheduler instance
scheduler = CandleCloseScheduler()
