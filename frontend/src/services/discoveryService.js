import { api } from './api.js';

export const startDiscovery = (spec) => api('/discovery', { method: 'POST', body: { spec } });
export const getJob = (id) => api(`/discovery/${id}`);
export const listJobs = () => api('/discovery');
export const compareCandidates = (ids) => api(`/candidates/compare?ids=${ids.join(',')}`);
