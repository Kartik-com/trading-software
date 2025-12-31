"""
Optional paper trading module for tracking hypothetical trades.
"""
from typing import List, Optional
from datetime import datetime
import logging

from models import PaperTrade, PaperTradingStats, Signal

logger = logging.getLogger(__name__)


class PaperTradingEngine:
    """
    Manages paper trading positions and tracks performance.
    """
    
    def __init__(self):
        self.trades: List[PaperTrade] = []
        self.open_trades: List[PaperTrade] = []
    
    def open_position(self, signal: Signal, quantity: float = 1.0) -> PaperTrade:
        """
        Open a new paper trading position based on a signal.
        
        Args:
            signal: Trading signal
            quantity: Hypothetical quantity
            
        Returns:
            PaperTrade object
        """
        trade = PaperTrade(
            symbol=signal.symbol,
            side=signal.signal_type if signal.signal_type != "REVERSAL" else "BUY",
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            quantity=quantity,
            entry_time=signal.candle_close_time
        )
        
        self.trades.append(trade)
        self.open_trades.append(trade)
        
        logger.info(f"Opened paper trade: {trade.side} {trade.symbol} @ {trade.entry_price}")
        
        return trade
    
    def update_positions(self, symbol: str, current_price: float):
        """
        Update open positions and close if stop loss hit.
        
        Args:
            symbol: Trading pair
            current_price: Current market price
        """
        for trade in self.open_trades[:]:  # Copy list to allow modification
            if trade.symbol != symbol:
                continue
            
            # Check if stop loss hit
            if trade.side == "BUY" and current_price <= trade.stop_loss:
                self.close_position(trade.id, current_price, "CLOSED_LOSS")
            elif trade.side == "SELL" and current_price >= trade.stop_loss:
                self.close_position(trade.id, current_price, "CLOSED_LOSS")
    
    def close_position(
        self,
        trade_id: str,
        exit_price: float,
        status: str = "CLOSED_MANUAL"
    ) -> Optional[PaperTrade]:
        """
        Close a paper trading position.
        
        Args:
            trade_id: Trade ID to close
            exit_price: Exit price
            status: Close status
            
        Returns:
            Closed trade or None
        """
        # Find the trade
        trade = None
        for t in self.open_trades:
            if t.id == trade_id:
                trade = t
                break
        
        if not trade:
            logger.warning(f"Trade {trade_id} not found")
            return None
        
        # Calculate PnL
        if trade.side == "BUY":
            pnl = (exit_price - trade.entry_price) * trade.quantity
        else:  # SELL
            pnl = (trade.entry_price - exit_price) * trade.quantity
        
        # Update trade
        trade.exit_price = exit_price
        trade.exit_time = datetime.utcnow()
        trade.pnl = pnl
        trade.status = status if pnl < 0 else "CLOSED_WIN"
        
        # Remove from open trades
        self.open_trades.remove(trade)
        
        logger.info(f"Closed paper trade: {trade.symbol} PnL: {pnl:.2f}")
        
        return trade
    
    def get_stats(self) -> PaperTradingStats:
        """
        Calculate paper trading statistics.
        
        Returns:
            PaperTradingStats object
        """
        closed_trades = [t for t in self.trades if t.status != "OPEN"]
        winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl and t.pnl < 0]
        
        total_pnl = sum(t.pnl for t in closed_trades if t.pnl)
        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0
        
        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        largest_win = max((t.pnl for t in winning_trades), default=0)
        largest_loss = min((t.pnl for t in losing_trades), default=0)
        
        return PaperTradingStats(
            total_trades=len(self.trades),
            open_trades=len(self.open_trades),
            closed_trades=len(closed_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            total_pnl=total_pnl,
            average_win=avg_win,
            average_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss
        )


# Global paper trading engine
paper_engine = PaperTradingEngine()
