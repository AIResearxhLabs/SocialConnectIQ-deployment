/**
 * StatusBadge — coloured pill for deployment/test/service statuses.
 */

const STATUS_STYLES = {
    // Deployment statuses
    pending:     'bg-yellow-900 text-yellow-300',
    running:     'bg-blue-900 text-blue-300 animate-pulse',
    approved:    'bg-teal-900 text-teal-300',
    success:     'bg-green-900 text-green-300',
    completed:   'bg-green-900 text-green-300',
    failed:      'bg-red-900 text-red-300',
    cancelled:   'bg-gray-700 text-gray-300',
    rolling_back:'bg-orange-900 text-orange-300',
    rolled_back: 'bg-orange-800 text-orange-200',
    rejected:    'bg-red-800 text-red-300',
    // Test statuses
    passed:      'bg-green-900 text-green-300',
    // Service health
    healthy:     'bg-green-900 text-green-300',
    unhealthy:   'bg-red-900 text-red-300',
    unknown:     'bg-gray-700 text-gray-400',
    // CI
    ci_pass:     'bg-green-900 text-green-300',
    ci_fail:     'bg-red-900 text-red-300',
    // GitHub run
    waiting:     'bg-yellow-900 text-yellow-300',
    in_progress: 'bg-blue-900 text-blue-300 animate-pulse',
};

export function StatusBadge({ status, className = '' }) {
    const style = STATUS_STYLES[status] || 'bg-gray-700 text-gray-300';
    return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${style} ${className}`}>
            {status?.replace(/_/g, ' ')}
        </span>
    );
}
