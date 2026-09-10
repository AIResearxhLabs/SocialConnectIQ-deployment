/**
 * Axios API client for the dashboard backend.
 *
 * Base URL defaults to same origin (via Vite proxy in dev,
 * or direct URL in production via VITE_API_URL env var).
 */

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '';

const apiClient = axios.create({
    baseURL: BASE_URL,
    headers: { 'Content-Type': 'application/json' },
    timeout: 15000,
});

// ─── Deployments ──────────────────────────────────────────────────────────────

export const fetchDeployments = (environment = null, limit = 50) => {
    const params = { limit };
    if (environment) params.environment = environment;
    return apiClient.get('/api/deployments', { params }).then(r => r.data);
};

export const fetchDeployment = (id) =>
    apiClient.get(`/api/deployments/${id}`).then(r => r.data);

export const triggerDeployment = (payload) =>
    apiClient.post('/api/deployments/trigger', payload).then(r => r.data);

export const approveDeployment = (id, action, approver, reason = '') =>
    apiClient.post(`/api/deployments/${id}/approve`, { action, approver, reason }).then(r => r.data);

export const cancelDeployment = (id) =>
    apiClient.delete(`/api/deployments/${id}`).then(r => r.data);

// ─── Test Runs ───────────────────────────────────────────────────────────────

export const fetchTestRuns = (runType = null, limit = 50) => {
    const params = { limit };
    if (runType) params.run_type = runType;
    return apiClient.get('/api/tests', { params }).then(r => r.data);
};

export const fetchTestRun = (id) =>
    apiClient.get(`/api/tests/${id}`).then(r => r.data);

export const triggerTestRun = (payload) =>
    apiClient.post('/api/tests/trigger', payload).then(r => r.data);

// ─── Health ───────────────────────────────────────────────────────────────────

export const fetchServicesHealth = () =>
    apiClient.get('/api/health/services').then(r => r.data);

export const fetchCIStatus = () =>
    apiClient.get('/api/health/ci-status').then(r => r.data);

export const fetchPendingGates = () =>
    apiClient.get('/api/health/pending-gates').then(r => r.data);
