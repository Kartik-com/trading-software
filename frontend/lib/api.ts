/**
 * API client for backend communication.
 * Handles all HTTP requests and WebSocket connections.
 */
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Types
export interface Signal {
    id: string;
    signal_type: 'BUY' | 'SELL' | 'REVERSAL';
    symbol: string;
    timeframe: string;
    bias: 'BULLISH' | 'BEARISH' | 'RANGE';
    structure: string;
    entry_price: number;
    stop_loss: number;
    take_profit?: number;
    confidence: 'LOW' | 'MEDIUM' | 'HIGH';
    candle_close_time: string;
    ema_alignment: boolean;
    rsi?: number;
    stoch_rsi_k?: number;
    stoch_rsi_d?: number;
    liquidity_sweep: boolean;
}

export interface MarketBias {
    symbol: string;
    timeframe: string;
    bias: 'BULLISH' | 'BEARISH' | 'RANGE';
    price: number;
    ema_20: number;
    ema_50: number;
    ema_100: number;
    ema_200: number;
    timestamp: string;
}

export interface PriceData {
    symbol: string;
    price: number;
    change_24h?: number;
    volume_24h?: number;
    timestamp: string;
}

export interface CandleDataPoint {
    timestamp: string | Date;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    ema_20?: number;
    ema_50?: number;
    ema_100?: number;
    ema_200?: number;
}

export interface SignalHistory {
    signals: Signal[];
    total: number;
}

// API Methods
export const api = {
    /**
     * Get list of monitored symbols
     */
    async getSymbols(): Promise<string[]> {
        const response = await apiClient.get<string[]>('/api/symbols');
        return response.data;
    },

    /**
     * Get recent signals
     */
    async getSignals(symbol?: string, limit: number = 50): Promise<SignalHistory> {
        const params: any = { limit };
        if (symbol) params.symbol = symbol;

        const response = await apiClient.get<SignalHistory>('/api/signals', { params });
        return response.data;
    },

    /**
     * Get market bias for a symbol
     */
    async getBias(symbol: string): Promise<MarketBias> {
        const response = await apiClient.get<MarketBias>(`/api/bias/${symbol}`);
        return response.data;
    },

    /**
     * Get current price data
     */
    async getPrice(symbol: string): Promise<PriceData> {
        const response = await apiClient.get<PriceData>(`/api/price/${symbol}`);
        return response.data;
    },

    /**
     * Get historical chart data
     */
    async getChartData(symbol: string): Promise<CandleDataPoint[]> {
        const response = await apiClient.get<CandleDataPoint[]>(`/api/chart/${symbol}`);
        return response.data;
    },
};

// WebSocket Manager
export class SignalWebSocket {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 3000;
    private onSignalCallback?: (signal: Signal) => void;

    constructor() {
        this.connect();
    }

    private connect() {
        // Use window.location.hostname to determine if we act as localhost or not
        // But here we rely on API_BASE_URL which is mostly sufficient
        // Replace http/https with ws/wss
        const wsUrl = API_BASE_URL.replace(/^http/, 'ws') + '/ws/signals';

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === 'signal' && this.onSignalCallback) {
                        this.onSignalCallback(data.data);
                    } else if (data.type === 'ping') {
                        // Respond to ping
                        this.ws?.send(JSON.stringify({ type: 'pong' }));
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.attemptReconnect();
            };
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            this.attemptReconnect();
        }
    }

    private attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.connect(), this.reconnectDelay);
        }
    }

    onSignal(callback: (signal: Signal) => void) {
        this.onSignalCallback = callback;
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

export default api;
