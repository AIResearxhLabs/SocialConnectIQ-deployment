import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Rocket, FlaskConical, HeartPulse, RotateCcw, ScrollText } from 'lucide-react';

const NAV = [
    { to: '/',         icon: LayoutDashboard, label: 'Overview',   desc: 'System status' },
    { to: '/deploy',   icon: Rocket,          label: 'Deploy',     desc: 'Trigger & approve' },
    { to: '/tests',    icon: FlaskConical,    label: 'Tests',      desc: '58 test scenarios' },
    { to: '/health',   icon: HeartPulse,      label: 'Health',     desc: 'Live monitoring' },
    { to: '/rollback', icon: RotateCcw,       label: 'Rollback',   desc: 'Emergency revert' },
    { to: '/logs',     icon: ScrollText,      label: 'Logs',       desc: 'Run history' },
];

export function Sidebar() {
    return (
        <aside style={{ background: 'var(--bg-surface)', borderRight: '1px solid var(--border-dim)' }}
            className="w-52 min-h-screen flex flex-col py-5 shrink-0">

            {/* Brand */}
            <div className="px-4 mb-6">
                <div className="flex items-center gap-2 mb-1">
                    <div className="w-6 h-6 rounded flex items-center justify-center"
                        style={{ background: 'rgba(56,139,253,0.15)', border: '1px solid rgba(56,139,253,0.3)' }}>
                        <span className="text-xs font-bold" style={{ color: 'var(--accent)' }}>S</span>
                    </div>
                    <span className="text-xs font-bold tracking-widest uppercase" style={{ color: 'var(--text-2)' }}>
                        SocialConnectIQ
                    </span>
                </div>
                <p className="text-xs ml-8" style={{ color: 'var(--text-3)' }}>DevOps Dashboard</p>
            </div>

            {/* Nav */}
            <nav className="flex flex-col gap-0.5 px-2 flex-1">
                {NAV.map(({ to, icon: Icon, label, desc }) => (
                    <NavLink key={to} to={to} end={to === '/'}
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-3 py-2.5 rounded text-sm transition-all group
                             ${isActive ? 'nav-active' : 'hover:bg-white/5'}`
                        }>
                        {({ isActive }) => (
                            <>
                                <Icon size={15} style={{ color: isActive ? 'var(--accent)' : 'var(--text-3)' }}
                                    className="shrink-0 group-hover:text-[var(--text-2)] transition-colors" />
                                <div>
                                    <div style={{ color: isActive ? 'var(--accent)' : 'var(--text-1)' }}
                                        className="text-sm font-medium leading-none">{label}</div>
                                    <div className="text-xs mt-0.5" style={{ color: 'var(--text-3)' }}>{desc}</div>
                                </div>
                            </>
                        )}
                    </NavLink>
                ))}
            </nav>

            {/* Footer */}
            <div className="px-4 pt-4" style={{ borderTop: '1px solid var(--border-dim)' }}>
                <p className="mono text-xs" style={{ color: 'var(--text-3)' }}>v1.0.0 · CP-31</p>
            </div>
        </aside>
    );
}
