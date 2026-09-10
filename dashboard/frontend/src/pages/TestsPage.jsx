import { useEffect, useState } from 'react';
import { FlaskConical, Play, ExternalLink } from 'lucide-react';
import { fetchTestRuns, triggerTestRun } from '../api/client.js';
import { StatusBadge } from '../components/StatusBadge.jsx';

const RUN_TYPES = [
    { value: 'ci',         label: 'CI (lint + unit + docker)' },
    { value: 'regression', label: 'Regression (58 workflow tests)' },
    { value: 'smoke',      label: 'Smoke (production health)' },
];

export function TestsPage() {
    const [runs, setRuns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [form, setForm] = useState({ run_type: 'ci', version: '' });
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState('');

    const load = () => {
        setLoading(true);
        fetchTestRuns(null, 20).then(setRuns).catch(console.error).finally(() => setLoading(false));
    };
    useEffect(load, []);

    const submit = async (e) => {
        e.preventDefault();
        setSubmitting(true); setError('');
        try {
            await triggerTestRun({ ...form, environment: 'staging', triggered_by: 'dashboard-user' });
            load();
        } catch (err) {
            setError(err.response?.data?.detail || err.message);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="p-6 space-y-6">
            {/* Suite overview */}
            <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-200 mb-3">58 Workflow Test Scenarios</h3>
                <div className="flex flex-wrap gap-2">
                    {['Auth(7)','OAuth(12)','Posting(11)','Scheduling(5)','Analytics(4)',
                      'Trending(5)','UserMgmt(4)','Billing(4)','Health(6)'].map(s => (
                        <span key={s} className="bg-gray-900 border border-gray-700 rounded-full px-3 py-1 text-xs text-gray-300">
                            WF-{s}
                        </span>
                    ))}
                </div>
            </div>

            {/* Trigger form */}
            <form onSubmit={submit} className="bg-gray-800 rounded-xl p-6 border border-gray-700 space-y-4">
                <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
                    <FlaskConical size={16} className="text-purple-400" /> Trigger Test Run
                </h3>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-xs text-gray-400 mb-1">Test Type</label>
                        <select className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200"
                            value={form.run_type}
                            onChange={e => setForm(f => ({ ...f, run_type: e.target.value }))}>
                            {RUN_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs text-gray-400 mb-1">Version (optional)</label>
                        <input className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200"
                            placeholder="1.3.0-abc1234"
                            value={form.version}
                            onChange={e => setForm(f => ({ ...f, version: e.target.value }))} />
                    </div>
                </div>
                {error && <p className="text-xs text-red-400">{error}</p>}
                <button type="submit" disabled={submitting}
                    className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-lg text-sm font-medium">
                    <Play size={14} /> {submitting ? 'Triggering…' : 'Run Tests'}
                </button>
            </form>

            {/* History */}
            <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <div className="flex justify-between mb-4">
                    <h3 className="text-sm font-semibold text-gray-200">Test Run History</h3>
                    <button onClick={load} className="text-xs text-gray-500 hover:text-gray-300">Refresh</button>
                </div>
                {loading && <p className="text-xs text-gray-500">Loading…</p>}
                {!loading && runs.length === 0 && <p className="text-xs text-gray-500">No test runs yet.</p>}
                {!loading && runs.map(r => (
                    <div key={r.id} className="py-3 border-b border-gray-700 last:border-0 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <StatusBadge status={r.status} />
                            <span className="text-sm text-gray-200">{r.run_type}</span>
                            {r.total_tests != null && (
                                <span className="text-xs text-gray-500">{r.passed_tests}/{r.total_tests} passed</span>
                            )}
                        </div>
                        <div className="flex items-center gap-2">
                            {r.github_run_url && (
                                <a href={r.github_run_url} target="_blank" rel="noopener noreferrer"
                                    className="text-xs text-blue-400 flex items-center gap-1">
                                    <ExternalLink size={12} /> Actions
                                </a>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
