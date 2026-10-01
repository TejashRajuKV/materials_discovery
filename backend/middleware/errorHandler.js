import { logger } from '../utils/logger.js';

export function notFound(req, res) {
  res.status(404).json({ error: `Not found: ${req.method} ${req.originalUrl}` });
}

// eslint-disable-next-line no-unused-vars
export function errorHandler(err, req, res, next) {
  if (err.type === 'entity.parse.failed') return res.status(400).json({ error: 'Invalid JSON body' });
  const status = err.status || 500;
  if (status >= 500) logger.error(err);
  res.status(status).json({ error: status >= 500 && !err.status ? 'Internal server error' : err.message, details: err.details });
}
