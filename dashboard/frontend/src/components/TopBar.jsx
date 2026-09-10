/**
 * TopBar — displays page title, WebSocket connection status,
 * and a global pending-gates alert badge.
 */

import { Wifi, WifiOff, AlertTriangle } from 'lucide-react';

export function TopBar({ title, wsStatus, pendingCount = 0 }) {
    const isConnected = wsStatus === 'open';

    return (
        <header className="h-14 bg-gray-900 border-b border-gray-800 flex items-center px-6 gap-4 shrink-0">
            <h2 className="text-base font-semibold text-gray-100 flex-1">{title}</h2>

            {/* Pending human gates alert */}
            {pendingCount > 0 && (
                <div className="flex items-center gap-1.5 bg-yellow-900/60 text-yellow-300 text-xs px-3 py-1.5 rounded-full border border-yellow-700">
                    <AlertTriangle size={13} />
                    {pendingCount} gate{pendingCount > 1 ? 's' : ''} waiting
                </div>
            )}

            {/* WebSocket status */}
            <div
                className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded
                    ${isConnected ? 'text-green-400' : 'text-red-400'}`}
                title={`WebSocket: ${wsStatus}`}
            >
                {isConnected ? <Wifi size={13} /> : <WifiOff size={13} />}
                {isConnected ? 'Live' : 'Offline'}
            </div>
        </header>
    );
}
