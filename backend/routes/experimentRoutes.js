import { Router } from 'express';
import * as c from '../controllers/experimentController.js';

export default (db) => {
  const r = Router();
  r.get('/experiments', c.experiments(db));
  r.get('/models', c.models(db));
  r.get('/models/:id', c.model(db));
  return r;
};
