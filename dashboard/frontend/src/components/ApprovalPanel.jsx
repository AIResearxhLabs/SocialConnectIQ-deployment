import { useState } from 'react';
import { CheckCircle, XCircle } from 'lucide-react';
import { approveDeployment } from '../api/client.js';

export function ApprovalPanel({ deployment, onAction }) {
    const [approver, setApprover] = useState('');
    const [loading, setLoading] = useState('');

    const handleAction = async (action) => {
        if (!approver.trim()) { alert('Enter your name/email first.'); return; }
        setLoading(action);
        try {
            await approveDeployment(deployment.id, action, approver);
            onAction();
        } catch (err) {
            alert(err.message);
        } finally {
            setLoading('');
        }
    };

    return (
        <div className="bg-yellow-900/30 border border-yellow-700 rounded-xl p-4 mt-2">
            <p className="text-yellow-300 text-sm font-medium mb-3">
                ⏸ Awaiting approval: <span className="font-normal">{deployment.approval_gate}</span>
            </p>
            <input
                className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200 mb-3"
                placeholder="Your name / email"
                value={approver}
                onChange={e => setApprover(e.target.value)}
            />
            <div className="flex gap-3">
                <button onClick={() => handleAction('approve')} disabled={!!loading}
                    className="flex items-center gap-1.5 bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-xs font-medium">
                    <CheckCircle size={13} /> {loading === 'approve' ? 'Approving…' : 'Approve'}
                </button>
                <button onClick={() => handleAction('reject')} disabled={!!loading}
                    className="flex items-center gap-1.5 bg-red-700 hover:bg-red-600 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-xs font-medium">
                    <XCircle size={13} /> {loading === 'reject' ? 'Rejecting…' : 'Reject'}
                </button>
                <button onClick={() => handleAction('rollback')} disabled={!!loading}
                    className="flex items-center gap-1.5 bg-orange-700 hover:bg-orange-600 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-xs font-medium">
                    {loading === 'rollback' ? 'Triggering…' : '↩ Rollback'}
                </button>
            </div>
        </div>
    );
}
