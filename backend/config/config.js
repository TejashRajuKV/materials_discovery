import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

export const config = {
  root,
  port: Number(process.env.PORT) || 3000,
  dbPath: process.env.DB_PATH || path.join(root, 'database', 'materials.db'),
  pythonBin: process.env.PYTHON_BIN || 'python3',
  mlEntry: path.join(root, 'ml', 'main.py'),
  exportPath: path.join(root, 'ml', 'data', 'processed', 'export.json'),
  mlTimeoutMs: Number(process.env.ML_TIMEOUT_MS) || 120_000,
  maxFormulasPerRequest: 200,
  maxConcurrentJobs: Number(process.env.MAX_CONCURRENT_JOBS) || 2,
  rateLimit: {
    windowMs: 60_000,
    predictPerWindow: Number(process.env.RATE_LIMIT_PREDICT) || 60,
    discoveryPerWindow: Number(process.env.RATE_LIMIT_DISCOVERY) || 10,
  },
  backupsDir: path.join(root, 'database', 'backups'),
  backupsToKeep: 7,
};
