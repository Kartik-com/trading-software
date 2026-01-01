"""
FastAPI application - main entry point for the trading analysis backend.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import List, Optional, Dict, Any
import asyncio
import json
import pandas as pd
from datetime import datetime

import config
from models import Signal, MarketBias, PriceData, SignalHistory
from scanner import scanner
from alerts import alert_service
from timeframe import scheduler
import indicators

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


manager = ConnectionManager()


# Callback for candle closes
async def on_candle_close(timeframe: str, timestamp):
    """
    Called when a candle closes. Scans for signals and sends alerts.
    """
    logger.info(f"Scanning {timeframe} candles at {timestamp.isoformat()}")
    
    try:
        # Scan all symbols
        signals = await scanner.scan_all_symbols(timeframe)
        
        if signals:
            logger.info(f"Found {len(signals)} signals on {timeframe}")
            
            # Send Telegram alerts
            sent_count = await alert_service.send_batch_alerts(signals)
            logger.info(f"Sent {sent_count} Telegram alerts")
            
            # Broadcast to WebSocket clients
            for signal in signals:
                await manager.broadcast({
                    "type": "signal",
                    "data": signal.model_dump(mode='json')
                })
        
    except Exception as e:
        logger.error(f"Error in candle close callback: {e}", exc_info=True)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown logic.
    """
    # Startup
    logger.info("Starting trading analysis system...")
    
    # Register callbacks for each timeframe
    scheduler.register_callback(config.ENTRY_TIMEFRAME, on_candle_close)
    scheduler.register_callback(config.BIAS_TIMEFRAME, on_candle_close)
    
    # Start the scheduler
    scheduler_task = asyncio.create_task(scheduler.run())
    
    # Send test Telegram message - DISABLED for production
    # if config.TELEGRAM_ENABLED:
    #     await alert_service.send_test_message()
        
    # Run INITIAL SCAN immediately for the last closed candle
    # This ensures the user sees state immediately without waiting 15 mins
    logger.info("Running initial startup scan in 2 seconds...")
    await asyncio.sleep(2)
    try:
        await scanner.scan_all_symbols(config.ENTRY_TIMEFRAME)
        await scanner.scan_all_symbols(config.BIAS_TIMEFRAME)
        logger.info("Initial startup scan completed")
    except Exception as e:
        logger.error(f"Initial scan failed: {e}")
    
    logger.info("System started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    scheduler.stop()
    await scheduler_task
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Crypto Trading Analysis API",
    description="Real-time cryptocurrency market analysis with Smart Money Concepts",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
# In production, we allow the specific Vercel origin and all for setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://trading-software-lemon.vercel.app",
        "*"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
    expose_headers=["*"],
)


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "exchange": config.EXCHANGE,
        "symbols": config.SYMBOLS,
        "telegram_enabled": config.TELEGRAM_ENABLED
    }


@app.get("/api/symbols", response_model=List[str])
async def get_symbols():
    """Get list of monitored symbols."""
    return config.SYMBOLS


@app.get("/api/signals", response_model=SignalHistory)
async def get_signals(symbol: Optional[str] = None, limit: int = 50):
    """
    Get recent signals.
    Args:
        symbol: Filter by symbol (optional)
        limit: Maximum number of signals to return
    """
    signals = scanner.signal_history
    
    # Filter by symbol if provided
    if symbol:
        signals = [s for s in signals if s.symbol == symbol]
    
    # Sort by timestamp (newest first)
    signals = sorted(signals, key=lambda x: x.candle_close_time, reverse=True)
    
    # Limit results
    signals = signals[:limit]
    
    return SignalHistory(
        signals=signals,
        total=len(signals)
    )


@app.get("/api/bias/{symbol:path}", response_model=MarketBias)
async def get_bias(symbol: str):
    """
    Get current market bias for a symbol.
    Args:
        symbol: Trading pair (e.g., BTC/USDT)
    """
    # Validate symbol - check strict equality if possible or just existence
    if symbol not in config.SYMBOLS:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not monitored")
    
    bias = await scanner.get_current_bias(symbol)
    
    if bias is None:
        raise HTTPException(status_code=500, detail="Failed to fetch market data")
    
    return bias


@app.get("/api/price/{symbol:path}", response_model=PriceData)
async def get_price(symbol: str):
    """
    Get current price data for a symbol.
    Args:
        symbol: Trading pair
    """
    if symbol not in config.SYMBOLS:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not monitored")
    
    try:
        # Fetch latest data
        df = await scanner.fetch_ohlcv(symbol, config.ENTRY_TIMEFRAME)
        
        if df is None or len(df) == 0:
            raise HTTPException(status_code=500, detail="Failed to fetch price data")
        
        latest = df.iloc[-1]
        
        # Calculate 24h change if we have enough data
        change_24h = None
        if len(df) >= 96:  # 24 hours of 15m candles
            price_24h_ago = df.iloc[-96]['close']
            change_24h = ((latest['close'] - price_24h_ago) / price_24h_ago) * 100
        
        return PriceData(
            symbol=symbol,
            price=latest['close'],
            change_24h=change_24h,
            volume_24h=df.tail(96)['volume'].sum() if len(df) >= 96 else None,
            timestamp=latest['timestamp'].to_pydatetime()
        )
        
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chart/{symbol:path}")
async def get_chart_data(symbol: str):
    """
    Get historical chart data with indicators for a symbol.
    Args:
        symbol: Trading pair
    """
    if symbol not in config.SYMBOLS:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not monitored")

    try:
        # Fetch data
        df = await scanner.fetch_ohlcv(symbol, config.ENTRY_TIMEFRAME, limit=300)
        
        if df is None or len(df) == 0:
            raise HTTPException(status_code=500, detail="Failed to fetch chart data")
        
        # Add indicators
        df = indicators.add_all_indicators(df)
        
        # Replace NaN with None for JSON serialization
        df = df.where(pd.notnull(df), None)
        
        # Convert to list of dicts
        records = df.to_dict('records')
        
        return records

    except Exception as e:
        logger.error(f"Error fetching chart data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    """
    WebSocket endpoint for real-time signal updates.
    """
    await manager.connect(websocket)
    
    try:
        # Send initial data
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to signal stream"
        })
        
        # Keep connection alive
        while True:
            # Wait for client messages (ping/pong)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo back to keep connection alive
                await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                # Send ping to check if client is still connected
                await websocket.send_json({"type": "ping"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Test signal endpoint REMOVED for production safety as per user request.
# No test signals will be generated.


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )
