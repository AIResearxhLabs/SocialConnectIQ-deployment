import { useEffect, useState } from 'react';
import { ScrollText, ExternalLink } from 'lucide-react';
import { fetchDeployments, fetchTestRuns } from '../api/client.js';
import { StatusBadge } from '../components/StatusBadge.jsx';

function RunList({ items, selected, onSelect, loading }) {
    if (loading) return <p className="text-xs text-gray-500 p-4">Loading…</p>;
    if (items.length === 0) return <p className="text-xs text-gray-500 p-4">None yet.</p>;
    return items.map(item => (
        <button key={item.id} onClick={() => onSelect(item.id)}
            className={`w-full text-left px-4 py-3 border-b border-gray-700 last:border-0 hover:bg-gray-700 ${selected === item.id ? 'bg-gray-700' : ''}`}>
            <div className="flex items-center justify-between mb-1">
                <StatusBadge status={item.status} />
                <span className="text-xs text-gray-600 font-mono">{item.id}</span>
            </div>
            <p className="text-xs text-gray-300">
                {item.version ? `v${item.version} · ${item.environment}` : `${item.run_type}`}
            </p>
        </button>
    ));
}

export function LogsPage() {
    const [deployments, setDeployments] = useState([]);
    const [testRuns, setTestRuns] = useState([]);
    const [selected, setSelected] = useState(null);
    const [tab, setTab] = useState('deployments');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        Promise.all([fetchDeployments(null, 30), fetchTestRuns(null, 30)])
            .then(([deps, tests]) => { setDeployments(deps); setTestRuns(tests); })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const items = tab === 'deployments' ? deployments : testRuns;
    const sel = selected ? items.find(i => i.id === selected) : null;

    return (
        <div className="p-6 space-y-4">
            <div className="flex items-center gap-2">
                {['deployments', 'tests'].map(t => (
                    <button key={t} onClick={() => { setTab(t); setSelected(null); }}
                        className={`text-sm px-4 py-2 rounded-lg capitalize ${tab === t ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-gray-200'}`}>
                        {t}
                    </button>
                ))}
            </div>

            <div className="grid grid-cols-3 gap-4 h-[560px]">
                <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden flex flex-col">
                    <div className="p-3 border-b border-gray-700 text-xs font-semibold text-gray-400 uppercase tracking-wide">{tab}</div>
                    <div className="overflow-y-auto flex-1 log-scroll">
                        <RunList items={items} selected={selected} onSelect={setSelected} loading={loading} />
                    </div>
                </div>

                <div className="col-span-2 bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                    {!sel ? (
                        <div className="flex flex-col items-center justify-center h-full text-gray-500">
                            <ScrollText size={28} className="mb-2 opacity-30" />
                            <p className="text-sm">Select a run</p>
                        </div>
                    ) : (
                        <div className="p-5 space-y-4 overflow-y-auto h-full log-scroll">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <StatusBadge status={sel.status} />
                                    <span className="font-mono text-sm text-gray-200">{sel.id}</span>
                                </div>
                                {sel.github_run_url && (
                                    <a href={sel.github_run_url} target="_blank" rel="noopener noreferrer"
                                        className="text-xs text-blue-400 flex items-center gap-1">
                                        <ExternalLink size={12} /> GitHub Actions
                                    </a>
                                )}
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-xs">
                                {[['Environment', sel.environment], ['Version', sel.version],
                                  ['By', sel.triggered_by], ['Duration', sel.duration_seconds ? `${sel.duration_seconds.toFixed(1)}s` : '—']]
                                  .filter(([,v]) => v).map(([k, v]) => (
                                    <div key={k} className="bg-gray-900 rounded p-3">
                                        <p className="text-gray-500 mb-0.5">{k}</p>
                                        <p className="text-gray-200 truncate">{v}</p>
                                    </div>
                                ))}
                            </div>
                            {sel.error_message && (
                                <div className="bg-red-950 border border-red-800 rounded p-3">
                                    <p className="text-xs text-red-400 font-mono">{sel.error_message}</p>
                                </div>
                            )}
                            <div className="bg-gray-950 rounded p-3">
                                <p className="text-xs text-gray-500">
                                    Full logs in GitHub Actions.
                                    {sel.github_run_url && <a href={sel.github_run_url} target="_blank"
                                        rel="noopener noreferrer" className="text-blue-400 underline ml-1">Open ↗</a>}
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
