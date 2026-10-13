import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { config } from '../config/config.js';
import { openDb } from './connection.js';

/** Load ml/data/processed/export.json (from `python ml/main.py export`) into SQLite. Idempotent. */
export function seed(db, exportPath = config.exportPath) {
  if (!fs.existsSync(exportPath)) {
    throw new Error(`${exportPath} not found. Run \`npm run ml:bootstrap\` first.`);
  }
  const { materials, properties = [], model } = JSON.parse(fs.readFileSync(exportPath, 'utf8'));

  const upsertMaterial = db.prepare(`
    INSERT INTO materials (formula, band_gap, source, predicted_band_gap, uncertainty)
    VALUES (@formula, @band_gap, @source, @predicted_band_gap, @uncertainty)
    ON CONFLICT(formula) DO UPDATE SET band_gap = excluded.band_gap, source = excluded.source,
      predicted_band_gap = excluded.predicted_band_gap, uncertainty = excluded.uncertainty`);
  const upsertProperty = db.prepare(`
    INSERT INTO material_properties (formula, property, unit, recorded, predicted, uncertainty,
      interval_low, interval_high, model_version)
    VALUES (@formula, @property, @unit, @recorded, @predicted, @uncertainty,
      @interval_low, @interval_high, @model_version)
    ON CONFLICT(formula, property) DO UPDATE SET unit = excluded.unit, recorded = excluded.recorded,
      predicted = excluded.predicted, uncertainty = excluded.uncertainty, interval_low = excluded.interval_low,
      interval_high = excluded.interval_high, model_version = excluded.model_version`);
  const insertModel = db.prepare(`
    INSERT INTO models (name, version, target_property, algorithm, metrics, details, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(version) DO UPDATE SET metrics = excluded.metrics, details = excluded.details,
      algorithm = excluded.algorithm`);
  const { results, ...details } = model;

  db.transaction(() => {
    for (const m of materials) upsertMaterial.run(m);
    for (const p of properties) {
      // node:sqlite rejects unused named parameters, so pass exactly the columns the statement uses.
      upsertProperty.run({
        formula: p.formula, property: p.property, unit: p.unit, recorded: p.recorded, predicted: p.predicted,
        uncertainty: p.uncertainty, interval_low: p.interval_low, interval_high: p.interval_high,
        model_version: p.model_version,
      });
    }
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
  return { materials: materials.length, properties: properties.length, modelVersion: model.version };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const db = openDb(config.dbPath);
  console.log('seeded', seed(db));
}
