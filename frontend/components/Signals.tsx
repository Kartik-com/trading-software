'use client';

import React from 'react';
import { Signal } from '@/lib/api';

interface SignalsProps {
    signals: Signal[];
}

const Signals: React.FC<SignalsProps> = ({ signals }) => {
    const formatPrice = (price: number) => {
        return '$' + price.toFixed(2);
    };

    const formatTime = (timestamp: string) => {
        const date = new Date(timestamp);

        const year = date.getUTCFullYear();
        const month = String(date.getUTCMonth() + 1).padStart(2, '0');
        const day = String(date.getUTCDate()).padStart(2, '0');
        const hours = String(date.getUTCHours()).padStart(2, '0');
        const minutes = String(date.getUTCMinutes()).padStart(2, '0');

        return `${year}-${month}-${day} ${hours}:${minutes} UTC`;
    };

    const getSignalEmoji = (type: string) => {
        switch (type) {
            case 'BUY':
                return '🟢';
            case 'SELL':
                return '🔴';
            case 'REVERSAL':
                return '🔄';
            default:
                return '⚪';
        }
    };

    if (signals.length === 0) {
        return (
            <div className="card">
                <div className="card-header">
                    <h2 className="card-title">Recent Signals</h2>
                </div>
                <div className="empty-state">
                    <div className="empty-state-icon">📊</div>
                    <p>No signals yet. Waiting for market opportunities...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="card">
            <div className="card-header">
                <h2 className="card-title">Recent Signals</h2>
                <span className="text-sm text-secondary">{signals.length} signals</span>
            </div>

            <div style={{ maxHeight: '80vh', overflowY: 'auto' }}>
                {signals.map((signal) => (
                    <div
                        key={signal.id}
                        className={`signal-card ${signal.signal_type.toLowerCase()}`}
                    >
                        <div className="signal-header">
                            <div className="signal-symbol">
                                {getSignalEmoji(signal.signal_type)} {signal.symbol}
                            </div>
                            <span className={`signal-type ${signal.signal_type.toLowerCase()}`}>
                                {signal.signal_type}
                            </span>
                        </div>

                        <div className="signal-details">
                            <div className="signal-detail">
                                <span className="signal-detail-label">Entry Price</span>
                                <span className="signal-detail-value">{formatPrice(signal.entry_price)}</span>
                            </div>

                            <div className="signal-detail">
                                <span className="signal-detail-label">Target</span>
                                <span className="signal-detail-value">{signal.take_profit ? formatPrice(signal.take_profit) : 'N/A'}</span>
                            </div>

                            <div className="signal-detail">
                                <span className="signal-detail-label">Stop Loss</span>
                                <span className="signal-detail-value">{formatPrice(signal.stop_loss)}</span>
                            </div>

                            <div className="signal-detail">
                                <span className="signal-detail-label">Timeframe</span>
                                <span className="signal-detail-value">{signal.timeframe}</span>
                            </div>

                            <div className="signal-detail">
                                <span className="signal-detail-label">Bias</span>
                                <span className="signal-detail-value">{signal.bias}</span>
                            </div>

                            <div className="signal-detail" style={{ gridColumn: '1 / -1' }}>
                                <span className="signal-detail-label">Structure</span>
                                <span className="signal-detail-value">{signal.structure}</span>
                            </div>

                            <div className="signal-detail">
                                <span className="signal-detail-label">Confidence</span>
                                <span className={`confidence-badge confidence-${signal.confidence.toLowerCase()}`}>
                                    {signal.confidence}
                                </span>
                            </div>

                            <div className="signal-detail">
                                <span className="signal-detail-label">Candle Close</span>
                                <span className="signal-detail-value" style={{ fontSize: '0.75rem' }}>
                                    {formatTime(signal.candle_close_time)}
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Signals;
