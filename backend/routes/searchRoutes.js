import { Router } from 'express';
import * as c from '../controllers/searchController.js';

export default (db, ml) => {
  const r = Router();
  r.get('/', c.list(db));
  r.post('/', c.create(db));
  r.post('/:id/run', c.run(db, ml));
  r.delete('/:id', c.remove(db));
  return r;
};
