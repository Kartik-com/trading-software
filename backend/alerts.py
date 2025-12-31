"""
Telegram alert system for sending trading signals.
"""
import logging
from typing import Optional
from telegram import Bot
from telegram.error import TelegramError
import asyncio

import config
from models import Signal, AlertMessage

logger = logging.getLogger(__name__)


class TelegramAlertService:
    """
    Manages Telegram bot and sends alerts.
    """
    
    def __init__(self):
        self.bot: Optional[Bot] = None
        self.chat_id: Optional[str] = None
        self.enabled = False
        
        if config.TELEGRAM_ENABLED:
            try:
                self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
                self.chat_id = config.TELEGRAM_CHAT_ID
                self.enabled = True
                logger.info("Telegram alert service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.enabled = False
        else:
            logger.warning("Telegram not configured - alerts disabled")
    
    async def send_signal_alert(self, signal: Signal) -> bool:
        """
        Send a trading signal alert via Telegram.
        
        Args:
            signal: Signal to send
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.debug("Telegram disabled, skipping alert")
            return False
        
        try:
            # Format the alert message
            alert = AlertMessage(signal=signal)
            message = alert.format()
            
            # Send to Telegram
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"Alert sent: {signal.signal_type} {signal.symbol}")
            return True
            
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending alert: {e}", exc_info=True)
            return False
    
    async def send_batch_alerts(self, signals: list[Signal]) -> int:
        """
        Send multiple alerts with rate limiting.
        
        Args:
            signals: List of signals to send
            
        Returns:
            Number of alerts sent successfully
        """
        sent_count = 0
        
        for signal in signals:
            success = await self.send_signal_alert(signal)
            if success:
                sent_count += 1
            
            # Rate limiting: wait between messages
            if len(signals) > 1:
                await asyncio.sleep(0.5)
        
        return sent_count
    
    async def send_test_message(self) -> bool:
        """
        Send a test message to verify Telegram configuration.
        
        Returns:
            True if test successful
        """
        if not self.enabled:
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text="🤖 Trading Analysis System - Test Message\n\nTelegram alerts are configured correctly!"
            )
            logger.info("Test message sent successfully")
            return True
        except Exception as e:
            logger.error(f"Test message failed: {e}")
            return False


# Global alert service instance
alert_service = TelegramAlertService()
