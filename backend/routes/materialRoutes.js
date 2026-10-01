import { Router } from 'express';
import * as c from '../controllers/materialController.js';

export default (db) => {
  const r = Router();
  r.get('/', c.list(db));
  r.get('/stats', c.stats(db));
  r.get('/:id', c.get(db));
  return r;
};
