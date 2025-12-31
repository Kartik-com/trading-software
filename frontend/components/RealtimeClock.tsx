'use client';

import React, { useState, useEffect } from 'react';

const RealtimeClock = () => {
    const [time, setTime] = useState<Date | null>(null);

    useEffect(() => {
        setTime(new Date());
        const timer = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    if (!time) return null;

    const formatTime = (date: Date, zone: string) => {
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
            timeZone: zone
        });
    };

    return (
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                <span style={{ fontWeight: 'bold', color: 'var(--text-primary)' }}>{formatTime(time, 'UTC')} UTC</span>
                <span>{formatTime(time, 'Asia/Kolkata')} IST</span>
            </div>
        </div>
    );
};

export default RealtimeClock;
