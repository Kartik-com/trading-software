'use client';

import React from 'react';
import { MarketBias } from '@/lib/api';

interface BiasIndicatorProps {
    bias: MarketBias | null;
    loading?: boolean;
}

const BiasIndicator: React.FC<BiasIndicatorProps> = ({ bias, loading }) => {
    if (loading) {
        return (
            <div className="card">
                <div className="loading">
                    <div className="spinner"></div>
                </div>
            </div>
        );
    }

    if (!bias) {
        return null;
    }

    const getBiasIcon = (biasType: string) => {
        switch (biasType) {
            case 'BULLISH':
                return '↗️';
            case 'BEARISH':
                return '↘️';
            case 'RANGE':
                return '↔️';
            default:
                return '⚪';
        }
    };

    const formatPrice = (price: number) => {
        return price.toFixed(2);
    };

    return (
        <div className="card">
            <div className="card-header">
                <h3 className="card-title">Market Bias (1H)</h3>
                <span className={`bias-indicator ${bias.bias.toLowerCase()}`}>
                    {getBiasIcon(bias.bias)} {bias.bias}
                </span>
            </div>

            <div style={{ marginTop: '1rem' }}>
                <div className="signal-detail" style={{ marginBottom: '1rem' }}>
                    <span className="signal-detail-label">Current Price</span>
                    <span className="signal-detail-value" style={{ fontSize: '1.5rem' }}>
                        ${formatPrice(bias.price)}
                    </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
                    <div className="signal-detail">
                        <span className="signal-detail-label">EMA 20</span>
                        <span className="signal-detail-value">${formatPrice(bias.ema_20)}</span>
                    </div>

                    <div className="signal-detail">
                        <span className="signal-detail-label">EMA 50</span>
                        <span className="signal-detail-value">${formatPrice(bias.ema_50)}</span>
                    </div>

                    <div className="signal-detail">
                        <span className="signal-detail-label">EMA 100</span>
                        <span className="signal-detail-value">${formatPrice(bias.ema_100)}</span>
                    </div>

                    <div className="signal-detail">
                        <span className="signal-detail-label">EMA 200</span>
                        <span className="signal-detail-value">${formatPrice(bias.ema_200)}</span>
                    </div>
                </div>

                <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Last updated: {new Date(bias.timestamp).toLocaleTimeString()}
                </div>
            </div>
        </div>
    );
};

export default BiasIndicator;
