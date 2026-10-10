import fs from 'node:fs';
import path from 'node:path';
import { config } from '../config/config.js';
import { HttpError } from '../utils/helpers.js';

// formula -> JARVIS jid of its most stable entry, read once from the stability table.
let jidByFormula = null;
function loadJids() {
  if (jidByFormula) return jidByFormula;
  jidByFormula = new Map();
  if (!fs.existsSync(config.stabilityPath)) return jidByFormula;
  const [header, ...rows] = fs.readFileSync(config.stabilityPath, 'utf8').trim().split('\n');
  const cols = header.split(',');
  const iFormula = cols.indexOf('formula');
  const iJid = cols.indexOf('jid');
  for (const line of rows) {
    const cells = line.split(',');  // formulas and jids contain no commas
    if (cells[iJid]) jidByFormula.set(cells[iFormula], cells[iJid]);
  }
  return jidByFormula;
}

/** Atomic structure of a material's most stable JARVIS entry (for the viewer). */
export function getStructure(db, id) {
  const material = getMaterial(db, id);
  const jid = loadJids().get(material.formula);
  if (!jid) throw new HttpError(404, `no crystal structure for ${material.formula}`);
  const file = path.join(config.structuresDir, `${jid}.json`);
  if (!fs.existsSync(file)) throw new HttpError(404, `structure file for ${jid} not found`);
  return { formula: material.formula, ...JSON.parse(fs.readFileSync(file, 'utf8')) };
}

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
  const properties = db.prepare('SELECT * FROM material_properties WHERE formula = ? ORDER BY property')
    .all(row.formula);
  return { ...row, properties };
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
