/**
 * Sidebar navigation for the DevOps dashboard.
 */

import { NavLink } from 'react-router-dom';
import {
    LayoutDashboard,
    Rocket,
    FlaskConical,
    HeartPulse,
    RotateCcw,
    ScrollText,
} from 'lucide-react';

const NAV_ITEMS = [
    { to: '/',           icon: LayoutDashboard, label: 'Overview' },
    { to: '/deploy',     icon: Rocket,          label: 'Deploy' },
    { to: '/tests',      icon: FlaskConical,     label: 'Run Tests' },
    { to: '/health',     icon: HeartPulse,       label: 'Health' },
    { to: '/rollback',   icon: RotateCcw,        label: 'Rollback' },
    { to: '/logs',       icon: ScrollText,       label: 'Logs' },
];

export function Sidebar() {
    return (
        <aside className="w-56 min-h-screen bg-gray-900 border-r border-gray-800 flex flex-col py-6 px-3 shrink-0">
            {/* Brand */}
            <div className="mb-8 px-3">
                <h1 className="text-sm font-bold text-blue-400 uppercase tracking-widest">SocialConnectIQ</h1>
                <p className="text-xs text-gray-500 mt-0.5">DevOps Dashboard</p>
            </div>

            {/* Nav */}
            <nav className="flex flex-col gap-1 flex-1">
                {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
                    <NavLink
                        key={to}
                        to={to}
                        end={to === '/'}
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors
                             ${isActive
                                ? 'bg-blue-600 text-white font-medium'
                                : 'text-gray-400 hover:bg-gray-800 hover:text-gray-100'}`
                        }
                    >
                        <Icon size={16} />
                        {label}
                    </NavLink>
                ))}
            </nav>

            {/* Footer */}
            <div className="mt-auto px-3 text-xs text-gray-600">v1.0 · DevOps Hub</div>
        </aside>
    );
}
