/** Reusable summary metric card. */
export function SummaryCard({ title, value, icon: Icon, color }) {
    return (
        <div className="bg-gray-800 rounded-xl p-5 flex items-start gap-4 border border-gray-700">
            <div className={`p-2.5 rounded-lg ${color}`}>
                <Icon size={20} className="text-white" />
            </div>
            <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide">{title}</p>
                <p className="text-2xl font-bold text-gray-100 mt-0.5">{value ?? '—'}</p>
            </div>
        </div>
    );
}
