import { useState } from 'react';
import { RotateCcw, AlertTriangle, Play } from 'lucide-react';
import { triggerDeployment } from '../api/client.js';

export function RollbackPage() {
    const [form, setForm] = useState({ service: 'all', reason: '' });
    const [status, setStatus] = useState('');
    const [loading, setLoading] = useState(false);

    const handleRollback = async (e) => {
        e.preventDefault();
        if (!confirm(`Roll back ${form.service}? This triggers Emergency Rollback workflow.`)) return;
        setLoading(true); setStatus('');
        try {
            // Rollback is triggered via the rollback workflow
            // We reuse triggerDeployment with a special flag here for demonstration
            // In production: call a dedicated /api/rollback endpoint
            await fetch('/api/deployments/trigger', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    environment: 'production',
                    version: 'rollback',
                    triggered_by: 'dashboard-rollback',
                }),
            });
            setStatus('✅ Rollback workflow triggered. Monitor progress in GitHub Actions.');
        } catch (err) {
            setStatus(`❌ Error: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 space-y-6">
            {/* Warning banner */}
            <div className="bg-orange-900/40 border border-orange-700 rounded-xl p-5 flex items-start gap-3">
                <AlertTriangle size={20} className="text-orange-400 shrink-0 mt-0.5" />
                <div>
                    <p className="text-orange-300 font-semibold text-sm">Emergency Rollback</p>
                    <p className="text-orange-400/80 text-xs mt-1">
                        This triggers the <code className="bg-orange-900 px-1 rounded">rollback.yml</code> workflow
                        which reverts Cloud Run traffic to the previous stable revision within 2 minutes.
                        Use only when services are down or critically broken.
                    </p>
                </div>
            </div>

            <form onSubmit={handleRollback} className="bg-gray-800 rounded-xl p-6 border border-gray-700 space-y-4">
                <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
                    <RotateCcw size={16} className="text-orange-400" /> Trigger Rollback
                </h3>
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Service</label>
                    <select className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200"
                        value={form.service}
                        onChange={e => setForm(f => ({ ...f, service: e.target.value }))}>
                        <option value="all">All Services</option>
                        <option value="api-gateway">api-gateway</option>
                        <option value="backend-service">backend-service</option>
                        <option value="integration-service">integration-service</option>
                        <option value="agent-service">agent-service</option>
                    </select>
                </div>
                <div>
                    <label className="block text-xs text-gray-400 mb-1">Reason (required)</label>
                    <textarea
                        required
                        className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200 min-h-[80px] resize-none"
                        placeholder="Describe the incident requiring rollback…"
                        value={form.reason}
                        onChange={e => setForm(f => ({ ...f, reason: e.target.value }))}
                    />
                </div>
                {status && (
                    <p className={`text-sm ${status.startsWith('✅') ? 'text-green-400' : 'text-red-400'}`}>{status}</p>
                )}
                <button type="submit" disabled={loading || !form.reason.trim()}
                    className="flex items-center gap-2 bg-orange-600 hover:bg-orange-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-lg text-sm font-medium">
                    <Play size={14} /> {loading ? 'Triggering…' : 'Execute Rollback'}
                </button>
            </form>

            {/* Manual gcloud commands */}
            <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                <h3 className="text-sm font-semibold text-gray-200 mb-4">Manual gcloud Rollback</h3>
                <p className="text-xs text-gray-400 mb-3">If GitHub Actions is unavailable, run these locally:</p>
                <pre className="bg-gray-950 rounded-lg p-4 text-xs text-green-400 overflow-x-auto">
{`# Get previous revision
gcloud run revisions list --service=api-gateway \\
  --region=us-central1 --sort-by='~metadata.creationTimestamp' --limit=3

# Rollback traffic
gcloud run services update-traffic api-gateway \\
  --to-revisions=<PREV_REVISION>=100 \\
  --region=us-central1 --project=socialconnectiq-488008`}
                </pre>
            </div>
        </div>
    );
}
