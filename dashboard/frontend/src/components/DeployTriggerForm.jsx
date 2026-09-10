import { useState } from 'react';
import { Rocket, Play } from 'lucide-react';
import { triggerDeployment } from '../api/client.js';

export function DeployTriggerForm({ onTriggered }) {
    const [form, setForm] = useState({
        environment: 'staging', version: '', initial_traffic_pct: '10', include_frontend: true
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const submit = async (e) => {
        e.preventDefault();
        if (!form.version.trim()) { setError('Version required.'); return; }
        setLoading(true); setError('');
        try {
            await triggerDeployment({ ...form, triggered_by: 'dashboard-user' });
            onTriggered();
        } catch (err) {
            setError(err.response?.data?.detail || err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={submit} className="bg-gray-800 rounded-xl p-6 border border-gray-700 space-y-4">
            <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
                <Rocket size={16} className="text-blue-400" /> Trigger Deployment
            </h3>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Environment</label>
                    <select
                        className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200"
                        value={form.environment}
                        onChange={e => setForm(f => ({ ...f, environment: e.target.value }))}>
                        <option value="staging">Staging</option>
                        <option value="production">Production</option>
                    </select>
                </div>
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Version</label>
                    <input
                        className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200"
                        placeholder="e.g. 1.3.0"
                        value={form.version}
                        onChange={e => setForm(f => ({ ...f, version: e.target.value }))} />
                </div>
            </div>
            {form.environment === 'production' && (
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Initial Traffic %</label>
                    <select className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200"
                        value={form.initial_traffic_pct}
                        onChange={e => setForm(f => ({ ...f, initial_traffic_pct: e.target.value }))}>
                        <option value="10">10%</option><option value="50">50%</option><option value="100">100%</option>
                    </select>
                </div>
            )}
            <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                <input type="checkbox" checked={form.include_frontend}
                    onChange={e => setForm(f => ({ ...f, include_frontend: e.target.checked }))} />
                Include frontend
            </label>
            {error && <p className="text-xs text-red-400">{error}</p>}
            <button type="submit" disabled={loading}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-lg text-sm font-medium">
                <Play size={14} /> {loading ? 'Triggering…' : 'Trigger Deployment'}
            </button>
        </form>
    );
}
