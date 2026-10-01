import { api, query } from './api.js';

export const listMaterials = (params, signal) => api(`/materials${query(params)}`, { signal });
export const getMaterial = (id) => api(`/materials/${id}`);
export const getMaterialStats = () => api('/materials/stats');
