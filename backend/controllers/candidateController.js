import * as service from '../services/discoveryService.js';
import { HttpError, toInt } from '../utils/helpers.js';

export const get = (db) => (req, res) => {
  const id = toInt(req.params.id, NaN);
  if (Number.isNaN(id)) throw new HttpError(400, 'id must be an integer');
  res.json(service.getCandidate(db, id));
};

export const compare = (db) => (req, res) => {
  const ids = String(req.query.ids ?? '').split(',').map((s) => toInt(s, NaN)).filter(Number.isFinite);
  if (ids.length < 2 || ids.length > 6) throw new HttpError(400, 'provide 2-6 candidate ids: ?ids=1,2,3');
  res.json(service.compareCandidates(db, ids));
};
