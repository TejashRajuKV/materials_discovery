import { HttpError } from '../utils/helpers.js';

const SORTS = {
  formula: 'formula ASC',
  band_gap: 'band_gap ASC',
  '-band_gap': 'band_gap DESC',
};

export function listMaterials(db, { q, minGap, maxGap, sort, limit, offset }) {
  const where = [];
  const params = {};
  if (q) { where.push('formula LIKE @q ESCAPE \'\\\''); params.q = `%${q.replace(/[\\%_]/g, '\\$&')}%`; }
  if (minGap !== undefined) { where.push('band_gap >= @minGap'); params.minGap = minGap; }
  if (maxGap !== undefined) { where.push('band_gap <= @maxGap'); params.maxGap = maxGap; }
  const clause = where.length ? `WHERE ${where.join(' AND ')}` : '';
  const orderBy = SORTS[sort] ?? SORTS.formula;
  const total = db.prepare(`SELECT COUNT(*) AS n FROM materials ${clause}`).get(params).n;
  const rows = db.prepare(`SELECT * FROM materials ${clause} ORDER BY ${orderBy} LIMIT @limit OFFSET @offset`)
    .all({ ...params, limit, offset });
  return { total, items: rows };
}

export function getMaterial(db, id) {
  const row = db.prepare('SELECT * FROM materials WHERE id = ?').get(id);
  if (!row) throw new HttpError(404, `material ${id} not found`);
  return row;
}

export function materialStats(db) {
  const summary = db.prepare(`SELECT COUNT(*) AS count, AVG(band_gap) AS mean_band_gap,
    MIN(band_gap) AS min_band_gap, MAX(band_gap) AS max_band_gap,
    AVG(band_gap = 0) AS fraction_zero_gap FROM materials`).get();
  const histogram = db.prepare(`SELECT MIN(CAST(band_gap / 0.5 AS INTEGER), 12) * 0.5 AS bin_start, COUNT(*) AS count
    FROM materials GROUP BY bin_start ORDER BY bin_start`).all();
  const sources = db.prepare('SELECT source, COUNT(*) AS count FROM materials GROUP BY source').all();
  return { ...summary, histogram, sources };
}
