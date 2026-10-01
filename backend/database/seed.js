import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { config } from '../config/config.js';
import { openDb } from './connection.js';

/** Load ml/data/processed/export.json (from `python ml/main.py export`) into SQLite. Idempotent. */
export function seed(db, exportPath = config.exportPath) {
  if (!fs.existsSync(exportPath)) {
    throw new Error(`${exportPath} not found. Run \`npm run ml:bootstrap\` first.`);
  }
  const { materials, model } = JSON.parse(fs.readFileSync(exportPath, 'utf8'));

  const upsertMaterial = db.prepare(`
    INSERT INTO materials (formula, band_gap, source, predicted_band_gap, uncertainty)
    VALUES (@formula, @band_gap, @source, @predicted_band_gap, @uncertainty)
    ON CONFLICT(formula) DO UPDATE SET band_gap = excluded.band_gap, source = excluded.source,
      predicted_band_gap = excluded.predicted_band_gap, uncertainty = excluded.uncertainty`);
  const insertModel = db.prepare(`
    INSERT OR IGNORE INTO models (name, version, target_property, algorithm, metrics, details, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)`);
  const { results, ...details } = model;

  db.transaction(() => {
    for (const m of materials) upsertMaterial.run(m);
    insertModel.run(`${model.target}-predictor`, model.version, model.target, model.best_model,
      JSON.stringify(results), JSON.stringify(details), model.trained_at);
    const modelRow = db.prepare('SELECT id FROM models WHERE version = ?').get(model.version);
    const exists = db.prepare('SELECT 1 FROM experiments WHERE model_id = ?').get(modelRow.id);
    if (!exists) {
      db.prepare('INSERT INTO experiments (name, model_id, dataset, metrics, notes) VALUES (?, ?, ?, ?, ?)')
        .run('001_baseline', modelRow.id, `${model.dataset_file} (${model.data_source.join(', ')})`,
          JSON.stringify(results), 'Baseline comparison: mean, ridge, random forest, gradient boosting.');
    }
  })();
  return { materials: materials.length, modelVersion: model.version };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const db = openDb(config.dbPath);
  console.log('seeded', seed(db));
}
