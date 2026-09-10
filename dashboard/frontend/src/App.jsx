import { Routes, Route, useLocation } from 'react-router-dom';
import { Sidebar } from './components/Sidebar.jsx';
import { TopBar } from './components/TopBar.jsx';
import { OverviewPage } from './pages/OverviewPage.jsx';
import { DeployPage } from './pages/DeployPage.jsx';
import { TestsPage } from './pages/TestsPage.jsx';
import { HealthPage } from './pages/HealthPage.jsx';
import { RollbackPage } from './pages/RollbackPage.jsx';
import { LogsPage } from './pages/LogsPage.jsx';
import { useWebSocket } from './hooks/useWebSocket.js';

const PAGE_TITLES = {
    '/':         'Overview',
    '/deploy':   'Deploy',
    '/tests':    'Run Tests',
    '/health':   'Health Monitor',
    '/rollback': 'Emergency Rollback',
    '/logs':     'Logs',
};

export default function App() {
    const { liveData, wsStatus } = useWebSocket();
    const location = useLocation();
    const title = PAGE_TITLES[location.pathname] || 'Dashboard';
    const pendingCount = (liveData?.pending_runs || []).length;

    return (
        <div className="flex min-h-screen bg-gray-950">
            <Sidebar />
            <div className="flex flex-col flex-1 min-w-0">
                <TopBar title={title} wsStatus={wsStatus} pendingCount={pendingCount} />
                <main className="flex-1 overflow-y-auto">
                    <Routes>
                        <Route path="/"         element={<OverviewPage liveData={liveData} />} />
                        <Route path="/deploy"   element={<DeployPage />} />
                        <Route path="/tests"    element={<TestsPage />} />
                        <Route path="/health"   element={<HealthPage liveData={liveData} />} />
                        <Route path="/rollback" element={<RollbackPage />} />
                        <Route path="/logs"     element={<LogsPage />} />
                    </Routes>
                </main>
            </div>
        </div>
    );
}
