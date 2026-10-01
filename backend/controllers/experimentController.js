import * as service from '../services/experimentService.js';
import { HttpError, toInt } from '../utils/helpers.js';

export const experiments = (db) => (req, res) => res.json(service.listExperiments(db));
export const models = (db) => (req, res) => res.json(service.listModels(db));
export const model = (db) => (req, res) => {
  const id = toInt(req.params.id, NaN);
  if (Number.isNaN(id)) throw new HttpError(400, 'id must be an integer');
  res.json(service.getModel(db, id));
};
