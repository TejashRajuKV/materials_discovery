import * as service from '../services/materialService.js';
import { HttpError, toInt, toNumber } from '../utils/helpers.js';

export const list = (db) => (req, res) => {
  const minGap = toNumber(req.query.min_gap);
  const maxGap = toNumber(req.query.max_gap);
  if (Number.isNaN(minGap) || Number.isNaN(maxGap)) throw new HttpError(400, 'min_gap/max_gap must be numbers');
  res.json(service.listMaterials(db, {
    q: String(req.query.q ?? '').trim().slice(0, 60),
    minGap, maxGap, sort: req.query.sort,
    limit: toInt(req.query.limit, 50, { min: 1, max: 200 }),
    offset: toInt(req.query.offset, 0),
  }));
};

export const get = (db) => (req, res) => {
  const id = toInt(req.params.id, NaN);
  if (Number.isNaN(id)) throw new HttpError(400, 'id must be an integer');
  res.json(service.getMaterial(db, id));
};

export const stats = (db) => (req, res) => res.json(service.materialStats(db));
