export async function predict(db, ml, formulas) {
  const { predictions } = await ml.predict(formulas);
  const insert = db.prepare(`INSERT INTO predictions (model_version, formula, prediction, uncertainty, confidence)
    VALUES (@model_version, @formula, @prediction, @uncertainty, @confidence)`);
  db.transaction(() => {
    for (const p of predictions) if (!p.error) insert.run(p);
  })();
  const known = db.prepare('SELECT band_gap FROM materials WHERE formula = ?');
  return predictions.map((p) => (p.error ? p : { ...p, known_band_gap: known.get(p.formula)?.band_gap ?? null }));
}

export function recentPredictions(db, limit = 20) {
  return db.prepare('SELECT * FROM predictions ORDER BY id DESC LIMIT ?').all(limit);
}
