import { api } from './api.js';

export const predict = (formulas, property = 'band_gap') => api('/predict', { method: 'POST', body: { formulas, property } });
export const explain = (formula) => api(`/predict/explain/${encodeURIComponent(formula)}`);
export const listModels = () => api('/models');
export const listExperiments = () => api('/experiments');
