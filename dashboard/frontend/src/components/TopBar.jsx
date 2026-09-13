import { Zap, ZapOff, AlertTriangle, GitBranch } from 'lucide-react';

export function TopBar({ title, wsStatus, pendingCount = 0 }) {
    const isLive = wsStatus === 'open';

    return (
        <header className="h-12 flex items-center px-5 gap-4 shrink-0"
            style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--border-dim)' }}>

            {/* Page title */}
            <div className="flex items-center gap-2 flex-1">
                <GitBranch size={14} style={{ color: 'var(--text-3)' }} />
                <h2 className="text-sm font-semibold" style={{ color: 'var(--text-1)' }}>{title}</h2>
            </div>

            {/* Pending gates badge */}
            {pendingCount > 0 && (
                <div className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full"
                    style={{ background: 'rgba(210,153,34,0.12)', border: '1px solid rgba(210,153,34,0.3)', color: 'var(--yellow)' }}>
                    <AlertTriangle size={11} />
                    {pendingCount} gate{pendingCount > 1 ? 's' : ''} awaiting approval
                </div>
            )}

            {/* Live indicator */}
            <div className="flex items-center gap-1.5 text-xs"
                style={{ color: isLive ? 'var(--green)' : 'var(--red)' }}
                title={`WebSocket: ${wsStatus}`}>
                <span className={`w-1.5 h-1.5 rounded-full inline-block ${isLive ? 'pulse-dot' : ''}`}
                    style={{ background: isLive ? 'var(--green)' : 'var(--red)' }} />
                {isLive ? 'Live' : wsStatus === 'connecting' ? 'Connecting…' : 'Offline'}
            </div>
        </header>
    );
}
