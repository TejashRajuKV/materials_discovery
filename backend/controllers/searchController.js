import * as service from '../services/searchService.js';
import { startJob } from '../services/discoveryService.js';
import { HttpError, toInt } from '../utils/helpers.js';

const idParam = (req) => {
  const id = toInt(req.params.id, NaN);
  if (Number.isNaN(id)) throw new HttpError(400, 'id must be an integer');
  return id;
};

export const list = (db) => (req, res) => res.json(service.listSearches(db));

export const create = (db) => (req, res) => {
  const { name, spec } = req.body ?? {};
  if (typeof name !== 'string' || !name.trim() || name.length > 80) {
    throw new HttpError(400, 'name is required (at most 80 characters)');
  }
  res.status(201).json(service.saveSearch(db, name.trim(), spec));
};

/** Start a discovery job from a saved spec. Returns the job, as POST /api/discovery does. */
export const run = (db, ml) => (req, res) => {
  const search = service.getSearch(db, idParam(req));
  const { job } = startJob(db, ml, search.spec, { generate: true, include_known: true });
  res.status(202).json(job);
};

export const remove = (db) => (req, res) => {
  service.deleteSearch(db, idParam(req));
  res.status(204).end();
};
