import { HttpError } from '../utils/helpers.js';

export function securityHeaders(req, res, next) {
  res.set({
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'no-referrer',
  });
  res.removeHeader('X-Powered-By');
  next();
}

/**
 * Fixed-window, in-memory, per-IP rate limiter. Fine for a single-process deployment;
 * put a shared store (or a reverse proxy) in front if the API is ever scaled out.
 */
export function rateLimit({ windowMs, max, now = Date.now }) {
  const hits = new Map();
  return (req, res, next) => {
    const key = req.ip;
    const t = now();
    let entry = hits.get(key);
    if (!entry || t >= entry.resetAt) {
      entry = { count: 0, resetAt: t + windowMs };
      hits.set(key, entry);
    }
    entry.count += 1;
    // Opportunistic cleanup so the map cannot grow without bound.
    if (hits.size > 10_000) for (const [k, v] of hits) if (t >= v.resetAt) hits.delete(k);

    res.set('X-RateLimit-Limit', String(max));
    res.set('X-RateLimit-Remaining', String(Math.max(0, max - entry.count)));
    if (entry.count > max) {
      res.set('Retry-After', String(Math.ceil((entry.resetAt - t) / 1000)));
      return next(new HttpError(429, 'Too many requests, slow down'));
    }
    next();
  };
}
