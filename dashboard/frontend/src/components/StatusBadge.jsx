const S = {
    pending:      { dot: '#d29922', text: '#d29922', bg: 'rgba(210,153,34,0.1)',  border: 'rgba(210,153,34,0.25)' },
    running:      { dot: '#388bfd', text: '#388bfd', bg: 'rgba(56,139,253,0.1)', border: 'rgba(56,139,253,0.25)', pulse: true },
    in_progress:  { dot: '#388bfd', text: '#388bfd', bg: 'rgba(56,139,253,0.1)', border: 'rgba(56,139,253,0.25)', pulse: true },
    approved:     { dot: '#3fb950', text: '#3fb950', bg: 'rgba(63,185,80,0.1)',  border: 'rgba(63,185,80,0.25)' },
    success:      { dot: '#3fb950', text: '#3fb950', bg: 'rgba(63,185,80,0.1)',  border: 'rgba(63,185,80,0.25)' },
    completed:    { dot: '#3fb950', text: '#3fb950', bg: 'rgba(63,185,80,0.1)',  border: 'rgba(63,185,80,0.25)' },
    passed:       { dot: '#3fb950', text: '#3fb950', bg: 'rgba(63,185,80,0.1)',  border: 'rgba(63,185,80,0.25)' },
    healthy:      { dot: '#3fb950', text: '#3fb950', bg: 'rgba(63,185,80,0.1)',  border: 'rgba(63,185,80,0.25)' },
    failed:       { dot: '#f85149', text: '#f85149', bg: 'rgba(248,81,73,0.1)',  border: 'rgba(248,81,73,0.25)' },
    unhealthy:    { dot: '#f85149', text: '#f85149', bg: 'rgba(248,81,73,0.1)',  border: 'rgba(248,81,73,0.25)' },
    rejected:     { dot: '#f85149', text: '#f85149', bg: 'rgba(248,81,73,0.1)',  border: 'rgba(248,81,73,0.25)' },
    rolling_back: { dot: '#db6d28', text: '#db6d28', bg: 'rgba(219,109,40,0.1)', border: 'rgba(219,109,40,0.25)' },
    rolled_back:  { dot: '#db6d28', text: '#db6d28', bg: 'rgba(219,109,40,0.1)', border: 'rgba(219,109,40,0.25)' },
    waiting:      { dot: '#d29922', text: '#d29922', bg: 'rgba(210,153,34,0.1)', border: 'rgba(210,153,34,0.25)' },
    cancelled:    { dot: '#484f58', text: '#8b949e', bg: 'rgba(72,79,88,0.1)',   border: 'rgba(72,79,88,0.3)' },
    unknown:      { dot: '#484f58', text: '#8b949e', bg: 'rgba(72,79,88,0.1)',   border: 'rgba(72,79,88,0.3)' },
    error:        { dot: '#f85149', text: '#f85149', bg: 'rgba(248,81,73,0.1)',  border: 'rgba(248,81,73,0.25)' },
};

export function StatusBadge({ status, className = '' }) {
    const s = S[status] || S.unknown;
    const label = status?.replace(/_/g, ' ') || '—';
    return (
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium mono ${className}`}
            style={{ background: s.bg, border: `1px solid ${s.border}`, color: s.text }}>
            <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${s.pulse ? 'pulse-dot' : ''}`}
                style={{ background: s.dot }} />
            {label}
        </span>
    );
}
