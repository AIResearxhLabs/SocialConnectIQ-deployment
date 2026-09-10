import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle, XCircle, Clock, Activity, AlertTriangle } from 'lucide-react';
import { fetchDeployments, fetchTestRuns, fetchCIStatus } from '../api/client.js';
import { StatusBadge } from '../components/StatusBadge.jsx';
import { SummaryCard } from '../components/SummaryCard.jsx';

const REPOS = ['SocialConnectIQ', 'SocialConnectIQ-frontend', 'MCPSocialTools'];

export function OverviewPage({ liveData }) {
    const [deployments, setDeployments] = useState([]);
    const [testRuns, setTestRuns] = useState([]);
    const [ciStatus, setCiStatus] = useState({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([fetchDeployments(null, 10), fetchTestRuns(null, 10), fetchCIStatus()])
            .then(([deps, tests, ci]) => {
                setDeployments(deps);
                setTestRuns(tests);
                setCiStatus(ci.repos || {});
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const serviceHealth = liveData?.service_health || [];
    const pendingCount = (liveData?.pending_runs || []).length;
    const successCount = deployments.filter(d => ['success', 'completed'].includes(d.status)).length;
    const failedCount = deployments.filter(d => d.status === 'failed').length;

    if (loading) return <div className="flex items-center justify-center h-64 text-gray-400">Loading…</div>;

    return (
        <div className="p-6 space-y-6">
            {pendingCount > 0 && (
                <div className="bg-yellow-900/40 border border-yellow-700 rounded-xl p-4 flex items-center gap-3">
                    <AlertTriangle size={18} className="text-yellow-400 shrink-0" />
                    <p className="text-yellow-300 text-sm">
                        {pendingCount} gate{pendingCount > 1 ? 's' : ''} waiting.{' '}
                        <Link to="/deploy" className="underline text-yellow-400">Review →</Link>
                    </p>
                </div>
            )}

            <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
                <SummaryCard title="Deployments" value={deployments.length} icon={Activity} color="bg-blue-600" />
                <SummaryCard title="Successful" value={successCount} icon={CheckCircle} color="bg-green-600" />
                <SummaryCard title="Failed" value={failedCount} icon={XCircle} color="bg-red-600" />
                <SummaryCard title="Test Runs" value={testRuns.length} icon={Clock} color="bg-purple-600" />
            </div>

            <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-200 mb-4">CI Status — main branch</h3>
                <div className="grid grid-cols-3 gap-3">
                    {REPOS.map(repo => (
                        <div key={repo} className="flex items-center justify-between bg-gray-900 rounded-lg px-4 py-3">
                            <span className="text-xs text-gray-300 truncate">{repo}</span>
                            <StatusBadge status={liveData?.ci_statuses?.[repo] ?? ciStatus[repo] ?? 'unknown'} />
                        </div>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-200 mb-4">Production Services</h3>
                    {serviceHealth.length === 0
                        ? <p className="text-xs text-gray-500">Connecting to live feed…</p>
                        : serviceHealth.map(svc => (
                            <div key={svc.name} className="flex items-center justify-between py-2 border-b border-gray-700 last:border-0">
                                <span className="text-sm text-gray-300">{svc.name}</span>
                                <div className="flex items-center gap-3">
                                    {svc.response_time_ms != null && <span className="text-xs text-gray-500">{svc.response_time_ms}ms</span>}
                                    <StatusBadge status={svc.status} />
                                </div>
                            </div>
                        ))
                    }
                </div>

                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-semibold text-gray-200">Recent Deployments</h3>
                        <Link to="/deploy" className="text-xs text-blue-400 hover:text-blue-300">View all →</Link>
                    </div>
                    {deployments.length === 0
                        ? <p className="text-xs text-gray-500">No deployments yet.</p>
                        : deployments.slice(0, 5).map(d => (
                            <div key={d.id} className="flex items-center justify-between py-2 border-b border-gray-700 last:border-0">
                                <div>
                                    <span className="text-sm text-gray-200">v{d.version}</span>
                                    <span className="text-xs text-gray-500 ml-2">{d.environment}</span>
                                </div>
                                <StatusBadge status={d.status} />
                            </div>
                        ))
                    }
                </div>
            </div>
        </div>
    );
}
