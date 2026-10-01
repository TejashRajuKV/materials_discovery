import { fileURLToPath } from 'node:url';
import cors from 'cors';
import express from 'express';
import { config } from './config/config.js';
import { openDb } from './database/connection.js';
import { errorHandler, notFound } from './middleware/errorHandler.js';
import candidateRoutes from './routes/candidateRoutes.js';
import discoveryRoutes from './routes/discoveryRoutes.js';
import experimentRoutes from './routes/experimentRoutes.js';
import materialRoutes from './routes/materialRoutes.js';
import predictionRoutes from './routes/predictionRoutes.js';
import { defaultMl } from './services/pythonService.js';
import { logger } from './utils/logger.js';

/** Build the app with injectable db / ML engine so tests need neither Python nor a file DB. */
export function createApp({ db, ml = defaultMl }) {
  const app = express();
  app.use(cors({ origin: process.env.CORS_ORIGIN || true }));
  app.use(express.json({ limit: '100kb' }));

  app.get('/api/health', (req, res) => res.json({ status: 'ok' }));
  app.use('/api/materials', materialRoutes(db));
  app.use('/api/predict', predictionRoutes(db, ml));
  app.use('/api/discovery', discoveryRoutes(db, ml));
  app.use('/api/candidates', candidateRoutes(db));
  app.use('/api', experimentRoutes(db));

  app.use(notFound);
  app.use(errorHandler);
  return app;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const db = openDb(config.dbPath);
  if (!db.prepare('SELECT 1 FROM materials LIMIT 1').get()) {
    logger.warn('materials table is empty — run `npm run ml:bootstrap && npm run db:seed`');
  }
  createApp({ db }).listen(config.port, () => logger.info(`API listening on :${config.port}`));
}
