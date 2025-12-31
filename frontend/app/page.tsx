'use client';

import React, { useState, useEffect } from 'react';
import Signals from '@/components/Signals';
import BiasIndicator from '@/components/BiasIndicator';
import RealtimeClock from '@/components/RealtimeClock';
import { api, Signal, MarketBias, SignalWebSocket } from '@/lib/api';

export default function Home() {
    const [symbols, setSymbols] = useState<string[]>([]);
    const [selectedSymbol, setSelectedSymbol] = useState<string>('');
    const [signals, setSignals] = useState<Signal[]>([]);
    const [bias, setBias] = useState<MarketBias | null>(null);
    const [loading, setLoading] = useState(true);
    const [wsConnected, setWsConnected] = useState(false);

    // Initialize WebSocket
    useEffect(() => {
        const ws = new SignalWebSocket();

        ws.onSignal((signal: Signal) => {
            console.log('New signal received:', signal);
            setSignals((prev) => [signal, ...prev]);

            // Show browser notification if permitted
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification(`${signal.signal_type} Signal - ${signal.symbol}`, {
                    body: `Entry: ${signal.entry_price} | Confidence: ${signal.confidence}`,
                    icon: '/favicon.ico',
                });
            }
        });

        setWsConnected(true);

        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }

        return () => {
            ws.disconnect();
        };
    }, []);

    // Load initial data
    useEffect(() => {
        const loadInitialData = async () => {
            try {
                // Get symbols
                const symbolsList = await api.getSymbols();
                setSymbols(symbolsList);

                if (symbolsList.length > 0) {
                    setSelectedSymbol(symbolsList[0]);
                }

                // Get recent signals
                const signalsData = await api.getSignals();
                setSignals(signalsData.signals);

                setLoading(false);
            } catch (error) {
                console.error('Error loading initial data:', error);
                setLoading(false);
            }
        };

        loadInitialData();
    }, []);

    // Load data for selected symbol
    useEffect(() => {
        if (!selectedSymbol) return;

        const loadSymbolData = async () => {
            try {
                // Get bias
                const biasData = await api.getBias(selectedSymbol);
                setBias(biasData);
            } catch (error) {
                console.error('Error loading symbol data:', error);
            }
        };

        loadSymbolData();

        // Refresh every 30 seconds
        const interval = setInterval(loadSymbolData, 30000);

        return () => clearInterval(interval);
    }, [selectedSymbol]);

    if (loading) {
        return (
            <div className="loading" style={{ height: '100vh' }}>
                <div className="spinner"></div>
            </div>
        );
    }

    return (
        <>
            <header className="header">
                <div className="container">
                    <div className="header-content">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <h1 className="header-title">Crypto Trading Analysis</h1>
                            <div className="status-indicator">
                                <div className="status-dot"></div>
                                <span>{wsConnected ? 'Live' : 'Connecting...'}</span>
                            </div>
                        </div>
                        <RealtimeClock />
                    </div>
                </div>
            </header>

            <main className="main">
                <div className="container">
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label htmlFor="symbol-select" style={{ marginRight: '0.75rem', color: 'var(--text-secondary)' }}>
                            Select Symbol:
                        </label>
                        <select
                            id="symbol-select"
                            value={selectedSymbol}
                            onChange={(e) => setSelectedSymbol(e.target.value)}
                        >
                            {symbols.map((symbol) => (
                                <option key={symbol} value={symbol}>
                                    {symbol}
                                </option>
                            ))}
                        </select>
                    </div>

                    <BiasIndicator bias={bias} />

                    <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr' }}>
                        <Signals signals={signals} />
                    </div>
                </div>
            </main>
        </>
    );
}
