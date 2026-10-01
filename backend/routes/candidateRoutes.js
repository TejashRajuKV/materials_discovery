import { Router } from 'express';
import * as c from '../controllers/candidateController.js';

export default (db) => {
  const r = Router();
  r.get('/compare', c.compare(db));
  r.get('/:id', c.get(db));
  return r;
};
