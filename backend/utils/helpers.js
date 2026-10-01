export const parseJson = (text, fallback = null) => {
  if (text == null) return fallback;
  try { return JSON.parse(text); } catch { return fallback; }
};

export class HttpError extends Error {
  constructor(status, message, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

export const toInt = (value, fallback, { min = 0, max = Number.MAX_SAFE_INTEGER } = {}) => {
  const n = Number.parseInt(value, 10);
  return Number.isFinite(n) ? Math.min(Math.max(n, min), max) : fallback;
};

export const toNumber = (value) => {
  if (value === undefined || value === '' || value === null) return undefined;
  const n = Number(value);
  return Number.isFinite(n) ? n : NaN;
};
