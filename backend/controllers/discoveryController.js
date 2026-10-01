import * as service from '../services/discoveryService.js';
import { HttpError, toInt } from '../utils/helpers.js';

const idParam = (req) => {
  const id = toInt(req.params.id, NaN);
  if (Number.isNaN(id)) throw new HttpError(400, 'id must be an integer');
  return id;
};

export const create = (db, ml) => (req, res) => {
  const { spec, generate, include_known: includeKnown } = req.body;
  const { job } = service.startJob(db, ml, spec, {
    generate: generate !== false,
    include_known: includeKnown !== false,
  });
  res.status(202).json(job);
};

export const list = (db) => (req, res) => res.json(service.listJobs(db));
export const get = (db) => (req, res) => res.json(service.getJobWithCandidates(db, idParam(req)));
