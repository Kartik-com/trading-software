'use client';

import React, { useEffect, useRef } from 'react';
import {
    createChart,
    IChartApi,
    ISeriesApi,
    CandlestickData,
    LineData,
    CrosshairMode
} from 'lightweight-charts';

interface CandleDataPoint {
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

interface ChartProps {
    symbol: string;
    data: CandleDataPoint[];
}

const Chart: React.FC<ChartProps> = ({ symbol, data }) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
    const emaSeriesRef = useRef<{
        ema20: ISeriesApi<'Line'> | null;
        ema50: ISeriesApi<'Line'> | null;
        ema100: ISeriesApi<'Line'> | null;
        ema200: ISeriesApi<'Line'> | null;
    }>({
        ema20: null,
        ema50: null,
        ema100: null,
        ema200: null,
    });

    // Initialize chart
    useEffect(() => {
        if (!chartContainerRef.current) return;

        try {
            // Create chart
            const chart = createChart(chartContainerRef.current, {
                width: chartContainerRef.current.clientWidth,
                height: 500,
                layout: {
                    background: { color: '#131827' },
                    textColor: '#9ca3af',
                },
                grid: {
                    vertLines: { color: '#1a1f35' },
                    horzLines: { color: '#1a1f35' },
                },
                crosshair: {
                    mode: CrosshairMode.Normal,
                },
                rightPriceScale: {
                    borderColor: '#2d3548',
                },
                timeScale: {
                    borderColor: '#2d3548',
                    timeVisible: true,
                    secondsVisible: false,
                },
            });

            chartRef.current = chart;

            // Add candlestick series
            const candleSeries = chart.addCandlestickSeries({
                upColor: '#10b981',
                downColor: '#ef4444',
                borderUpColor: '#10b981',
                borderDownColor: '#ef4444',
                wickUpColor: '#10b981',
                wickDownColor: '#ef4444',
            });

            candleSeriesRef.current = candleSeries;

            // Add EMA series
            emaSeriesRef.current.ema20 = chart.addLineSeries({
                color: '#3b82f6',
                lineWidth: 2,
                title: 'EMA 20',
            });

            emaSeriesRef.current.ema50 = chart.addLineSeries({
                color: '#8b5cf6',
                lineWidth: 2,
                title: 'EMA 50',
            });

            emaSeriesRef.current.ema100 = chart.addLineSeries({
                color: '#f59e0b',
                lineWidth: 1,
                title: 'EMA 100',
            });

            emaSeriesRef.current.ema200 = chart.addLineSeries({
                color: '#ef4444',
                lineWidth: 1,
                title: 'EMA 200',
            });

            // Handle resize
            const handleResize = () => {
                if (chartContainerRef.current && chartRef.current) {
                    chartRef.current.applyOptions({
                        width: chartContainerRef.current.clientWidth,
                    });
                }
            };

            window.addEventListener('resize', handleResize);

            return () => {
                window.removeEventListener('resize', handleResize);
                if (chartRef.current) {
                    chartRef.current.remove();
                }
            };
        } catch (error) {
            console.error('Error initializing chart:', error);
        }
    }, []);

    // Update chart data
    useEffect(() => {
        if (!data || data.length === 0) return;
        if (!candleSeriesRef.current) return;
        if (!chartRef.current) return;

        try {
            // Prepare candlestick data
            const candleData = data
                .filter((candle) => candle.open && candle.high && candle.low && candle.close)
                .map((candle) => {
                    const timestamp = typeof candle.timestamp === 'string'
                        ? new Date(candle.timestamp).getTime() / 1000
                        : candle.timestamp.getTime() / 1000;

                    return {
                        time: Math.floor(timestamp) as CandlestickData['time'],
                        open: candle.open,
                        high: candle.high,
                        low: candle.low,
                        close: candle.close,
                    };
                })
                .sort((a, b) => (a.time as number) - (b.time as number));

            if (candleData.length > 0) {
                candleSeriesRef.current.setData(candleData as CandlestickData[]);
            }

            // Prepare and set EMA data
            const prepareEmaData = (emaField: keyof CandleDataPoint) => {
                return data
                    .filter((candle) => candle[emaField] !== undefined && candle[emaField] !== null)
                    .map((candle) => {
                        const timestamp = typeof candle.timestamp === 'string'
                            ? new Date(candle.timestamp).getTime() / 1000
                            : candle.timestamp.getTime() / 1000;

                        return {
                            time: Math.floor(timestamp) as LineData['time'],
                            value: candle[emaField] as number,
                        };
                    })
                    .sort((a, b) => (a.time as number) - (b.time as number));
            };

            const ema20Data = prepareEmaData('ema_20');
            const ema50Data = prepareEmaData('ema_50');
            const ema100Data = prepareEmaData('ema_100');
            const ema200Data = prepareEmaData('ema_200');

            if (emaSeriesRef.current.ema20 && ema20Data.length > 0) {
                emaSeriesRef.current.ema20.setData(ema20Data as LineData[]);
            }
            if (emaSeriesRef.current.ema50 && ema50Data.length > 0) {
                emaSeriesRef.current.ema50.setData(ema50Data as LineData[]);
            }
            if (emaSeriesRef.current.ema100 && ema100Data.length > 0) {
                emaSeriesRef.current.ema100.setData(ema100Data as LineData[]);
            }
            if (emaSeriesRef.current.ema200 && ema200Data.length > 0) {
                emaSeriesRef.current.ema200.setData(ema200Data as LineData[]);
            }

            // Fit content
            chartRef.current.timeScale().fitContent();
        } catch (error) {
            console.error('Error updating chart data:', error);
        }
    }, [data]);

    return (
        <div className="card">
            <div className="card-header">
                <h2 className="card-title">{symbol} Chart</h2>
            </div>
            <div ref={chartContainerRef} className="chart-container" />
        </div>
    );
};

export default Chart;
