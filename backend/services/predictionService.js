export async function predict(db, ml, formulas, property = 'band_gap') {
  const { predictions } = await ml.predict(formulas, property);
  if (property !== 'band_gap') return predictions;  // only band-gap predictions are logged in `predictions`
  const insert = db.prepare(`INSERT INTO predictions (model_version, formula, prediction, uncertainty, confidence)
    VALUES (@model_version, @formula, @prediction, @uncertainty, @confidence)`);
  db.transaction(() => {
    for (const p of predictions) {
      if (p.error) continue;
      // node:sqlite rejects named parameters the statement does not use, so pass only the columns.
      insert.run({
        model_version: p.model_version, formula: p.formula, prediction: p.prediction,
        uncertainty: p.uncertainty, confidence: p.confidence,
      });
    }
  })();
  const known = db.prepare('SELECT band_gap FROM materials WHERE formula = ?');
  return predictions.map((p) => (p.error ? p : { ...p, known_band_gap: known.get(p.formula)?.band_gap ?? null }));
}

export function recentPredictions(db, limit = 20) {
  return db.prepare('SELECT * FROM predictions ORDER BY id DESC LIMIT ?').all(limit);
}
