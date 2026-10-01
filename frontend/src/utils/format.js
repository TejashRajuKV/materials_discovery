export const fmt = (value, digits = 2) => (value == null || Number.isNaN(value) ? '—' : Number(value).toFixed(digits));

export const metalLabel = (gap) => (gap === 0 ? 'metal / zero gap' : '');

/** Subscript digits in a formula: Fe2O3 -> Fe₂O₃ (display only). */
export const prettyFormula = (formula) => String(formula).replace(/\d/g, (d) => '₀₁₂₃₄₅₆₇₈₉'[d]);

export const parseElements = (text) => text.split(/[\s,]+/).map((s) => s.trim()).filter(Boolean);
