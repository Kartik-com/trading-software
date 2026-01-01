'use client';

import React, { useState, useEffect } from 'react';
import Signals from '@/components/Signals';
import BiasIndicator from '@/components/BiasIndicator';
import RealtimeClock from '@/components/RealtimeClock';
import { api, Signal, MarketBias, SignalWebSocket, ConnectionStatus } from '@/lib/api';

export default function Home() {
    const [symbols, setSymbols] = useState<string[]>([]);
    const [selectedSymbol, setSelectedSymbol] = useState<string>('');
    const [signals, setSignals] = useState<Signal[]>([]);
    const [bias, setBias] = useState<MarketBias | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [wsStatus, setWsStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);

    const loadInitialData = async (isManual = false) => {
        if (isManual) setRefreshing(true);
        try {
            // Get symbols
            const symbolsList = await api.getSymbols();
            setSymbols(symbolsList);

            if (symbolsList.length > 0 && !selectedSymbol) {
                setSelectedSymbol(symbolsList[0]);
            }

            // Get recent signals
            const signalsData = await api.getSignals();
            setSignals(signalsData.signals);

            setError(null);
        } catch (error) {
            console.error('Error loading initial data:', error);
            setError('Failed to connect to backend. It might be sleeping or deploying.');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    // Initialize WebSocket
    useEffect(() => {
        const ws = new SignalWebSocket();

        ws.onSignal((signal: Signal) => {
            console.log('New signal received:', signal);
            setSignals((prev) => {
                // Prevent duplicates in state
                if (prev.find(s => s.id === signal.id)) return prev;
                return [signal, ...prev];
            });

            // Show browser notification if permitted
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification(`${signal.signal_type} Signal - ${signal.symbol}`, {
                    body: `Entry: ${signal.entry_price} | Confidence: ${signal.confidence}`,
                    icon: '/favicon.ico',
                });
            }
        });

        ws.onStatusChange((status) => {
            setWsStatus(status);
        });

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

        // Refresh every 60 seconds
        const interval = setInterval(loadSymbolData, 60000);

        return () => clearInterval(interval);
    }, [selectedSymbol]);

    const getStatusInfo = (status: ConnectionStatus) => {
        switch (status) {
            case ConnectionStatus.CONNECTED:
                return { label: 'Live', color: '#10b981', dot: true };
            case ConnectionStatus.CONNECTING:
                return { label: 'Connecting...', color: '#f59e0b', dot: true };
            case ConnectionStatus.ERROR:
                return { label: 'Connect Error', color: '#ef4444', dot: false };
            case ConnectionStatus.DISCONNECTED:
                return { label: 'Disconnected', color: '#6b7280', dot: false };
            default:
                return { label: 'Unknown', color: '#6b7280', dot: false };
        }
    };

    const statusInfo = getStatusInfo(wsStatus);

    if (loading) {
        return (
            <div className="loading" style={{ height: '100vh' }}>
                <div className="spinner"></div>
                <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>Waking up backend...</p>
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
                            <div className="status-indicator" style={{
                                backgroundColor: `${statusInfo.color}15`,
                                color: statusInfo.color,
                                border: `1px solid ${statusInfo.color}30`
                            }}>
                                {statusInfo.dot && (
                                    <div className="status-dot" style={{
                                        backgroundColor: statusInfo.color,
                                        boxShadow: `0 0 10px ${statusInfo.color}`
                                    }}></div>
                                )}
                                <span>{statusInfo.label}</span>
                            </div>
                        </div>
                        <RealtimeClock />
                    </div>
                </div>
            </header>

            <main className="main">
                <div className="container">
                    {error && (
                        <div style={{
                            padding: '1rem',
                            backgroundColor: '#fee2e2',
                            color: '#b91c1c',
                            borderRadius: '0.5rem',
                            marginBottom: '1.5rem',
                            border: '1px solid #fecaca',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                        }}>
                            <span>{error}</span>
                            <button onClick={() => loadInitialData(true)} className="btn-secondary" style={{ padding: '0.25rem 0.75rem' }}>
                                Retry
                            </button>
                        </div>
                    )}

                    <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
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

                        <button
                            onClick={() => loadInitialData(true)}
                            className={`btn-secondary ${refreshing ? 'loading' : ''}`}
                            disabled={refreshing}
                        >
                            {refreshing ? 'Syncing...' : '🔄 Sync Signals'}
                        </button>
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
