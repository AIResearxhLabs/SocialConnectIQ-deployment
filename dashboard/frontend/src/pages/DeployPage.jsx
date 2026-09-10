import { useEffect, useState } from 'react';
import { ExternalLink, StopCircle } from 'lucide-react';
import { fetchDeployments, cancelDeployment } from '../api/client.js';
import { StatusBadge } from '../components/StatusBadge.jsx';
import { ApprovalPanel } from '../components/ApprovalPanel.jsx';
import { DeployTriggerForm } from '../components/DeployTriggerForm.jsx';

export function DeployPage() {
    const [deployments, setDeployments] = useState([]);
    const [loading, setLoading] = useState(true);

    const load = () => {
        setLoading(true);
        fetchDeployments(null, 20).then(setDeployments).catch(console.error).finally(() => setLoading(false));
    };
    useEffect(load, []);

    const handleCancel = async (id) => {
        if (!confirm('Cancel this deployment?')) return;
        await cancelDeployment(id).catch(console.error);
        load();
    };

    return (
        <div className="p-6 space-y-6">
            <DeployTriggerForm onTriggered={load} />

            <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <div className="flex justify-between mb-4">
                    <h3 className="text-sm font-semibold text-gray-200">Deployment History</h3>
                    <button onClick={load} className="text-xs text-gray-500 hover:text-gray-300">Refresh</button>
                </div>

                {loading && <p className="text-xs text-gray-500">Loading…</p>}
                {!loading && deployments.length === 0 && (
                    <p className="text-xs text-gray-500">No deployments yet.</p>
                )}
                {!loading && deployments.map(d => (
                    <div key={d.id} className="py-3 border-b border-gray-700 last:border-0">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <StatusBadge status={d.status} />
                                <span className="text-sm text-gray-200">v{d.version}</span>
                                <span className="text-xs text-gray-500">{d.environment}</span>
                                <span className="text-xs text-gray-600 font-mono">{d.id}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                {d.github_run_url && (
                                    <a href={d.github_run_url} target="_blank" rel="noopener noreferrer"
                                        className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
                                        <ExternalLink size={12} /> Actions
                                    </a>
                                )}
                                {['running', 'pending'].includes(d.status) && (
                                    <button onClick={() => handleCancel(d.id)}
                                        className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1">
                                        <StopCircle size={12} /> Cancel
                                    </button>
                                )}
                            </div>
                        </div>
                        {d.requires_approval && d.status === 'running' && (
                            <ApprovalPanel deployment={d} onAction={load} />
                        )}
                        {d.error_message && (
                            <p className="text-xs text-red-400 mt-1">{d.error_message}</p>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
