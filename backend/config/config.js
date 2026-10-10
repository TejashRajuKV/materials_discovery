import { resolvePython } from '../../scripts/python-bin.js';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

export const config = {
  root,
  port: Number(process.env.PORT) || 3000,
  dbPath: process.env.DB_PATH || path.join(root, 'database', 'materials.db'),
  pythonBin: resolvePython(),
  // Set to the resident ML service (python ml/service.py) to skip per-request model loading.
  mlServiceUrl: process.env.ML_SERVICE_URL || null,
  mlEntry: path.join(root, 'ml', 'main.py'),
  exportPath: path.join(root, 'ml', 'data', 'processed', 'export.json'),
  preprocessReportPath: path.join(root, 'ml', 'data', 'processed', 'preprocessing_report.json'),
  stabilityPath: path.join(root, 'ml', 'data', 'processed', 'stability.csv'),
  structuresDir: path.join(root, 'ml', 'data', 'processed', 'structures'),
  mlTimeoutMs: Number(process.env.ML_TIMEOUT_MS) || 600_000, // discovery loads the ~1 GB model bundle: ~150 s measured
  maxFormulasPerRequest: 200,
};
