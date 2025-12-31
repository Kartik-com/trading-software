"""
Market scanner - fetches data, analyzes markets, and generates signals.
STRICT SIGNAL LOGIC IMPLEMENTATION
"""
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import asyncio

import config
from models import Signal, MarketBias, Candle
from alerts import alert_service
import json
import os
# Import smc and indicators modules
import smc
import indicators

logger = logging.getLogger(__name__)


class MarketScanner:
    """
    Scans cryptocurrency markets and generates trading signals.
    Implements strict multi-timeframe analysis (1H Bias + 15m Entry).
    """
    
    def __init__(self):
        # Initialize exchange
        exchange_class = getattr(ccxt, config.EXCHANGE)
        self.exchange = exchange_class({
            'enableRateLimit': True,
        })
        
        # Signal history
        self.signal_history: List[Signal] = []
        self.history_file = os.path.join(os.path.dirname(__file__), "signals.json")
        self._load_history()
        
        # Last alert times (for deduplication)
        self.last_alert_times: Dict[str, datetime] = {}
        
        logger.info(f"Market scanner initialized with {config.EXCHANGE}")

    def _load_history(self):
        """Loads signal history from a JSON file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        # Convert ISO timestamp back to datetime
                        if 'candle_close_time' in item:
                            item['candle_close_time'] = datetime.fromisoformat(item['candle_close_time'])
                        self.signal_history.append(Signal(**item))
                logger.info(f"Loaded {len(self.signal_history)} signals from history file.")
            except Exception as e:
                logger.error(f"Error loading signal history: {e}")

    def _save_history(self):
        """Saves current signal history to a JSON file."""
        try:
            # Pydantic v2: model_dump(mode='json') correctly serializes datetimes to ISO strings
            data = [sig.model_dump(mode='json') for sig in self.signal_history]
                
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving signal history: {e}")
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = None) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data from exchange.
        """
        limit = limit or config.CANDLE_HISTORY_LIMIT
        try:
            # Fetch from exchange
            ohlcv = await asyncio.to_thread(
                self.exchange.fetch_ohlcv,
                symbol,
                timeframe,
                limit=limit
            )
            
            if not ohlcv:
                logger.warning(f"No data received for {symbol} {timeframe}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {symbol} {timeframe}: {e}", exc_info=True)
            return None
    
    def calculate_signal_score(
        self,
        structure_type: str,
        ema_aligned_count: int,
        rsi_valid: bool,
        stoch_valid: bool
    ) -> Tuple[int, str]:
        """
        Calculate signal confidence score based on USER PROVIDED SCRIPT rules.
        
        Points:
        - Structure: BOS (3 pts), CHoCH (2 pts)
        - EMA Alignment: 4/4 (2 pts), 3/4 (1 pt)
        - RSI Valid (1 pt)
        - Stoch Valid (1 pt)
        
        Levels:
        - HIGH: >= 6
        - MEDIUM: >= 4
        - LOW: < 4
        """
        score = 0
        
        # 1. Structure Score
        if "BOS" in structure_type:
            score += 3
        elif "CHOCH" in structure_type:
            score += 2
        
        # 2. EMA Score
        if ema_aligned_count >= 4:
            score += 2
        elif ema_aligned_count >= 3:
            score += 1
            
        # 3. Indicator Score
        if rsi_valid:
            score += 1
            
        if stoch_valid:
            score += 1
            
        # Determine Level
        if score >= 6:
            return score, "HIGH"
        elif score >= 4:
            return score, "MEDIUM"
        else:
            return score, "LOW"

    async def evaluate_symbol(self, symbol: str, timeframe: str) -> Optional[Signal]:
        """
        Evaluate a symbol for trading signals matching the USER SCRIPT EXACTLY.
        """
        try:
            # We only alert on the ENTRY_TIMEFRAME (15m) close.
            if timeframe != config.ENTRY_TIMEFRAME:
                return None
            
            # 1. Fetch Data (1H and 15m)
            # Use a slightly larger limit to ensure we have history
            df1h = await self.fetch_ohlcv(symbol, config.BIAS_TIMEFRAME, limit=210)
            df15 = await self.fetch_ohlcv(symbol, config.ENTRY_TIMEFRAME, limit=100)
            
            if df1h is None or df15 is None:
                return None
            
            # 2. Add Indicators
            df1h = indicators.add_all_indicators(df1h)
            df15 = indicators.add_all_indicators(df15)
            
            # --- REALTIME CANDLE SELECTION LOGIC ---
            # Determine which candle is the "Last Closed" one.
            # If the last row is very fresh (e.g. current minute), it's the Open candle.
            # If the last row is ~timeframe minutes old, it's the Closed candle.
            
            def get_closed_candle(df, tf_str):
                if len(df) < 2: return None
                last_row = df.iloc[-1]
                # If timestamp is the current open interval, use previous
                # Simple check: Compare with UTC now.
                now = datetime.utcnow()
                ts = last_row['timestamp'].to_pydatetime() if hasattr(last_row['timestamp'], 'to_pydatetime') else last_row['timestamp']
                
                # If candle is "future" or "now" relative to the close time expected?
                # E.g. 15m candle at 15:00 (Open time). Current time 15:00:05.
                # If candle timestamp is 15:00, it is the OPEN candle. We want 14:45.
                # Timedelta check:
                tf_minutes = 15 if "15m" in tf_str else 60
                elapsed = (now - ts).total_seconds() / 60
                
                if elapsed < tf_minutes:
                    # It's the current forming candle (or very recently closed?)
                    # Wait, timestamp is usually OPEN time.
                    # 15:00 candle opens at 15:00.
                    # If now is 15:00:05, elapsed is 0.05 min.
                    # This is the FORMING candle. We want `iloc[-2]`.
                    return df.iloc[-2], df 
                else:
                    # Candle is old enough to be closed?
                    # E.g. 14:45 candle. Now is 15:00:05. Elapsed is 15.05 min.
                    # It is the CLOSED candle (or the one that just closed).
                    return last_row, df

            last_1h, _ = get_closed_candle(df1h, config.BIAS_TIMEFRAME)
            last_15, df15_calc = get_closed_candle(df15, config.ENTRY_TIMEFRAME)

            if last_1h is None or last_15 is None: return None
            
            # 3. Determine Bias (1H)
            bias = "RANGE"
            if last_1h["close"] > last_1h["ema_200"]:
                bias = "BULLISH"
            elif last_1h["close"] < last_1h["ema_200"]:
                bias = "BEARISH"
                
            # 4. Determine Structure (15m)
            # Need to detect structure on the specific history associated with 'last_15'
            # If last_15 was iloc[-2], we slice df to encompass up to that point
            target_idx = last_15.name 
            try:
                loc_idx = df15_calc.index.get_loc(target_idx)
                df15_slice = df15_calc.iloc[:loc_idx+1]
            except:
                df15_slice = df15_calc 
            
            struct = smc.detect_structure(df15_slice)
            
            if not struct:
                logger.info(f"Scan {symbol} 15m: No Structure found.")
                return None
            
            # 5. Check EMA Alignment & Stoch RSI
            # Rules:
            # BUY: Close > All EMAs AND Stoch < 0.8
            # SELL: Close < All EMAs AND Stoch > 0.2
            
            ema_periods = [20, 50, 100, 200]
            close_price = last_15['close']
            
            ema_bull = all(close_price > last_15[f'ema_{p}'] for p in ema_periods if f'ema_{p}' in last_15)
            ema_bear = all(close_price < last_15[f'ema_{p}'] for p in ema_periods if f'ema_{p}' in last_15)
            
            stoch_k = last_15.get('stoch_rsi_k', 0.5)
            
            direction = None
            stop_loss = 0.0
            take_profit = 0.0
            atr = last_15.get('atr', 0) or (last_15['high'] - last_15['low'])
            atr_sl_mult = 1.5
            atr_tp_mult = 3.0 # 1:2 RR
            
            # BUY Logic
            if struct in ["BOS_BULL", "CHoCH_BULL"] and ema_bull and stoch_k < 80.0:
                direction = "BUY"
                stop_loss = close_price - (atr * atr_sl_mult)
                take_profit = close_price + (atr * atr_tp_mult)
                
            # SELL Logic
            elif struct in ["BOS_BEAR", "CHoCH_BEAR"] and ema_bear and stoch_k > 20.0:
                direction = "SELL"
                stop_loss = close_price + (atr * atr_sl_mult)
                take_profit = close_price - (atr * atr_tp_mult)
                
            if not direction:
                logger.info(f"Scan {symbol} 15m: Rejected. Structure {struct} but conditions not met (EMA/Stoch).")
                return None

            # 6. Calculate Confidence
            # Script logic: HIGH if BOS, MEDIUM if CHoCH? 
            # User script: confidence = "HIGH" if structure == "BOS_BULL" else "MEDIUM"
            
            confidence = "HIGH" if "BOS" in struct else "MEDIUM"
            
            # 7. Construct Signal
            signal = Signal(
                signal_type=direction,
                symbol=symbol,
                timeframe=config.ENTRY_TIMEFRAME,
                bias=bias,
                structure=f"{struct}",
                entry_price=float(close_price),
                stop_loss=float(stop_loss),
                take_profit=float(take_profit),
                confidence=confidence,
                candle_close_time=last_15['timestamp'].to_pydatetime() if hasattr(last_15['timestamp'], 'to_pydatetime') else last_15['timestamp'],
                ema_alignment=True, # Implicitly true since we checked it
                rsi=float(last_15['rsi']),
                stoch_rsi_k=float(stoch_k),
                stoch_rsi_d=float(last_15.get('stoch_rsi_d') or 0),
                liquidity_sweep=False
            )
            
            logger.info(f"Scan {symbol} 15m: MATCH! {direction} [{confidence}]")
            return signal
            
        except Exception as e:
            logger.error(f"Error evaluating {symbol} {timeframe}: {e}", exc_info=True)
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating {symbol} {timeframe}: {e}", exc_info=True)
            return None
    
    async def scan_all_symbols(self, timeframe: str) -> List[Signal]:
        """
        Scan all configured symbols for signals on the triggered timeframe.
        """
        signals = []
        
        # User script monitors both 15m and 1h. 
        # This function is called by scheduler when a 15m or 1h candle closes.
        
        # CASE 1: 15m Candle Close (ENTRY SIGNALS)
        if timeframe == config.ENTRY_TIMEFRAME:
            for symbol in config.SYMBOLS:
                try:
                    signal = await self.evaluate_symbol(symbol, timeframe)
                    if signal and self.should_send_alert(signal):
                        signals.append(signal)
                        self.signal_history.append(signal)
                        self._save_history()
                        logger.info(f"ENTRY SIGNAL: {signal.signal_type} {signal.symbol} {timeframe} [{signal.confidence}]")
                except Exception as e:
                    logger.error(f"Error scanning {symbol} for entries: {e}", exc_info=True)

        # CASE 2: 1H Candle Close (TREND REVERSAL ALERTS)
        elif timeframe == config.BIAS_TIMEFRAME:
            for symbol in config.SYMBOLS:
                try:
                    # Check for Bias Flip
                    market_bias = await self.get_current_bias(symbol)
                    if not market_bias: continue
                    
                    # We need to track state. For now, we compare with previous candle.
                    # Fetch 1H data (already fetched in get_current_bias but we need history)
                    df = await self.fetch_ohlcv(symbol, config.BIAS_TIMEFRAME)
                    if df is None or len(df) < 2: continue
                    
                    df = indicators.add_all_indicators(df)
                    
                    curr_candle = df.iloc[-1]
                    prev_candle = df.iloc[-2]
                    
                    # Determine Current & Previous Bias
                    curr_bias = "BULLISH" if curr_candle['close'] > curr_candle['ema_200'] else "BEARISH"
                    prev_bias = "BULLISH" if prev_candle['close'] > prev_candle['ema_200'] else "BEARISH"
                    
                    # If Bias has FLIPPED
                    if curr_bias != prev_bias:
                        # Add indicators to ensure ATR is present
                        atr_val = curr_candle['atr'] if 'atr' in curr_candle else (curr_candle['high'] - curr_candle['low'])
                        
                        sl_val = 0.0
                        tp_val = 0.0
                        if curr_bias == "BULLISH":
                            sl_val = curr_candle['close'] - (atr_val * 1.5)
                            tp_val = curr_candle['close'] + (atr_val * 3.0)
                        else:
                            sl_val = curr_candle['close'] + (atr_val * 1.5)
                            tp_val = curr_candle['close'] - (atr_val * 3.0)

                        # Create Reversal Signal
                        signal = Signal(
                            signal_type="REVERSAL",
                            symbol=symbol,
                            timeframe=config.BIAS_TIMEFRAME,
                            bias=curr_bias,
                            structure=f"Trend Flip: {prev_bias} -> {curr_bias}",
                            entry_price=float(curr_candle['close']),
                            stop_loss=float(sl_val),
                            take_profit=float(tp_val),
                            confidence="HIGH", # Reversals are critical
                            candle_close_time=curr_candle['timestamp'].to_pydatetime() if hasattr(curr_candle['timestamp'], 'to_pydatetime') else curr_candle['timestamp'],
                            ema_alignment=True, # It just happened
                            rsi=float(curr_candle.get('rsi', 0)),
                            stoch_rsi_k=float(curr_candle.get('stoch_rsi_k', 0)),
                            stoch_rsi_d=float(curr_candle.get('stoch_rsi_d', 0)),
                        )
                        
                        signals.append(signal)
                        self.signal_history.append(signal)
                        self._save_history()
                        logger.info(f"REVERSAL SIGNAL: {symbol} Flipped to {curr_bias}")
                        
                except Exception as e:
                    logger.error(f"Error scanning {symbol} for reversals: {e}", exc_info=True)
        
        return signals
    
    async def get_current_bias(self, symbol: str) -> Optional[MarketBias]:
        """
        Get current market bias using Simple User Logic (Close vs EMA 200).
        """
        try:
            df = await self.fetch_ohlcv(symbol, config.BIAS_TIMEFRAME)
            if df is None: return None
            
            # Add indicators
            df = indicators.add_all_indicators(df)
            latest = df.iloc[-1]
            
            # Determine Bias
            bias_str = "RANGE"
            if latest["close"] > latest["ema_200"]:
                bias_str = "BULLISH"
            elif latest["close"] < latest["ema_200"]:
                bias_str = "BEARISH"
            
            return MarketBias(
                symbol=symbol,
                timeframe=config.BIAS_TIMEFRAME,
                bias=bias_str,
                price=float(latest['close']),
                ema_20=float(latest['ema_20']),
                ema_50=float(latest['ema_50']),
                ema_100=float(latest['ema_100']),
                ema_200=float(latest['ema_200']),
                timestamp=latest['timestamp'].to_pydatetime() if hasattr(latest['timestamp'], 'to_pydatetime') else latest['timestamp']
            )
        except Exception as e:
            logger.error(f"Error getting bias for {symbol}: {e}")
            return None


# Global scanner instance
scanner = MarketScanner()
