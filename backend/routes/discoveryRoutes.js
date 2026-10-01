import { Router } from 'express';
import * as c from '../controllers/discoveryController.js';
import { validateDiscoveryBody } from '../middleware/validation.js';

export default (db, ml) => {
  const r = Router();
  r.post('/', validateDiscoveryBody, c.create(db, ml));
  r.get('/', c.list(db));
  r.get('/:id', c.get(db));
  return r;
};
