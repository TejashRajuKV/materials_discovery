import { api } from './api.js';

export const listSearches = () => api('/searches');
export const saveSearch = (name, spec) => api('/searches', { method: 'POST', body: { name, spec } });
export const runSearch = (id) => api(`/searches/${id}/run`, { method: 'POST', body: {} });
export const deleteSearch = (id) => api(`/searches/${id}`, { method: 'DELETE' });
