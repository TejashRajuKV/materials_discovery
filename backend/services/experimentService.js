import { HttpError, parseJson } from '../utils/helpers.js';

const modelView = (row) => row && { ...row, metrics: parseJson(row.metrics), details: parseJson(row.details) };

export function listModels(db) {
  return db.prepare('SELECT * FROM models ORDER BY id DESC').all().map(modelView);
}

export function getModel(db, id) {
  const row = db.prepare('SELECT * FROM models WHERE id = ?').get(id);
  if (!row) throw new HttpError(404, `model ${id} not found`);
  return modelView(row);
}

export function listExperiments(db) {
  return db.prepare(`SELECT e.*, m.version AS model_version, m.algorithm FROM experiments e
    LEFT JOIN models m ON m.id = e.model_id ORDER BY e.id DESC`).all()
    .map((r) => ({ ...r, metrics: parseJson(r.metrics) }));
}
