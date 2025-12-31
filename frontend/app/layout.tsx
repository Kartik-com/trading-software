import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
    title: 'Crypto Trading Analysis',
    description: 'Real-time cryptocurrency market analysis with Smart Money Concepts',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body>{children}</body>
        </html>
    )
}
