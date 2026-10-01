import { api } from './api.js';

export const predict = (formulas) => api('/predict', { method: 'POST', body: { formulas } });
export const explain = (formula) => api(`/predict/explain/${encodeURIComponent(formula)}`);
export const listModels = () => api('/models');
export const listExperiments = () => api('/experiments');
