/** Reusable card section with header label + optional right content. */
export function Section({ label, right, children, className = '' }) {
    return (
        <div className={`rounded-lg p-4 ${className}`}
            style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-dim)' }}>
            <div className="flex items-center justify-between mb-3">
                <span className="mono text-xs uppercase tracking-wider font-semibold"
                    style={{ color: 'var(--text-2)' }}>{label}</span>
                {right && <span className="text-xs" style={{ color: 'var(--text-3)' }}>{right}</span>}
            </div>
            {children}
        </div>
    );
}

/** Bordered row inside a section. */
export function Row({ children, last = false }) {
    return (
        <div className="flex items-center justify-between py-2"
            style={last ? {} : { borderBottom: '1px solid var(--border-dim)' }}>
            {children}
        </div>
    );
}

/** Metric card. */
export function Metric({ label, value, sub, icon: Icon, color }) {
    return (
        <div className="rounded-lg p-4 flex flex-col gap-2"
            style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-dim)' }}>
            <div className="flex items-center justify-between">
                <span className="mono text-xs uppercase tracking-wider" style={{ color: 'var(--text-3)' }}>{label}</span>
                {Icon && <Icon size={13} style={{ color }} />}
            </div>
            <span className="text-3xl font-bold" style={{ color: 'var(--text-1)' }}>{value ?? '—'}</span>
            {sub && <span className="text-xs" style={{ color: 'var(--text-3)' }}>{sub}</span>}
        </div>
    );
}

/** Full-width spinner/loading state. */
export function Loading() {
    return (
        <div className="flex items-center justify-center h-48 gap-3" style={{ color: 'var(--text-3)' }}>
            <div className="w-4 h-4 rounded-full border-2 spin"
                style={{ borderColor: 'var(--accent)', borderTopColor: 'transparent' }} />
            Loading…
        </div>
    );
}

/** Empty state placeholder. */
export function Empty({ message = 'No data yet.' }) {
    return <p className="text-xs py-3 text-center" style={{ color: 'var(--text-3)' }}>{message}</p>;
}
