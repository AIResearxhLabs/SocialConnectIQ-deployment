import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { fetchServicesHealth, fetchCIStatus, fetchPendingGates } from '../api/client.js';
import { StatusBadge } from '../components/StatusBadge.jsx';

const GCP_LINKS = {
    'Cloud Run':        'https://console.cloud.google.com/run?project=socialconnectiq-488008',
    'Cloud Logging':    'https://console.cloud.google.com/logs?project=socialconnectiq-488008',
    'Artifact Registry':'https://console.cloud.google.com/artifacts?project=socialconnectiq-488008',
    'Firebase Console': 'https://console.firebase.google.com/project/socialconnectiq-488008',
    'GitHub Actions':   'https://github.com/AIResearxhLabs/SocialConnectIQ-deployment/actions',
};

export function HealthPage({ liveData }) {
    const [services, setServices] = useState([]);
    const [ciStatus, setCiStatus] = useState({});
    const [pendingGates, setPendingGates] = useState([]);
    const [loading, setLoading] = useState(true);

    const load = () => {
        setLoading(true);
        Promise.all([fetchServicesHealth(), fetchCIStatus(), fetchPendingGates()])
            .then(([svc, ci, gates]) => {
                setServices(svc.services || []);
                setCiStatus(ci.repos || {});
                setPendingGates(gates.pending_runs || []);
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    };
    useEffect(load, []);

    const health = (liveData?.service_health?.length > 0) ? liveData.service_health : services;

    return (
        <div className="p-6 space-y-6">
            {/* Service Health */}
            <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-gray-200">Production Service Health</h3>
                    <button onClick={load} className="text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1">
                        <RefreshCw size={12} /> Refresh
                    </button>
                </div>
                {loading && <p className="text-xs text-gray-500">Checking…</p>}
                {!loading && health.length === 0 && <p className="text-xs text-gray-500">No data yet.</p>}
                <div className="grid grid-cols-2 gap-3">
                    {health.map(svc => (
                        <div key={svc.name} className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                            <div className="flex items-center justify-between mb-1">
                                <span className="text-sm font-medium text-gray-200">{svc.name}</span>
                                <StatusBadge status={svc.status} />
                            </div>
                            <p className="text-xs text-gray-500 truncate">{svc.url}</p>
                            {svc.response_time_ms != null && (
                                <p className="text-xs text-gray-400 mt-1">{svc.response_time_ms}ms</p>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Pending Gates */}
            {pendingGates.length > 0 && (
                <div className="bg-yellow-900/30 border border-yellow-700 rounded-xl p-5">
                    <h3 className="text-sm font-semibold text-yellow-300 mb-3">
                        ⏸ Pending Human Gates ({pendingGates.length})
                    </h3>
                    {pendingGates.map(r => (
                        <div key={r.id} className="flex items-center justify-between py-2 border-b border-yellow-900 last:border-0">
                            <span className="text-sm text-yellow-200">{r.workflow}</span>
                            <a href={r.html_url} target="_blank" rel="noopener noreferrer"
                                className="text-xs text-yellow-400 hover:text-yellow-200 underline">
                                Review in GitHub →
                            </a>
                        </div>
                    ))}
                </div>
            )}

            {/* CI Status */}
            <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-200 mb-4">CI Pipeline Status</h3>
                {Object.entries(ciStatus).map(([repo, status]) => (
                    <div key={repo} className="flex items-center justify-between py-2 border-b border-gray-700 last:border-0">
                        <span className="text-sm text-gray-300">{repo}</span>
                        <StatusBadge status={status || 'unknown'} />
                    </div>
                ))}
            </div>

            {/* GCP Links */}
            <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-200 mb-4">Quick Links</h3>
                <div className="grid grid-cols-2 gap-2">
                    {Object.entries(GCP_LINKS).map(([label, url]) => (
                        <a key={label} href={url} target="_blank" rel="noopener noreferrer"
                            className="flex items-center gap-2 bg-gray-900 hover:bg-gray-700 rounded-lg px-4 py-2.5 text-xs text-gray-300 hover:text-gray-100 transition-colors border border-gray-700">
                            {label} ↗
                        </a>
                    ))}
                </div>
            </div>
        </div>
    );
}
