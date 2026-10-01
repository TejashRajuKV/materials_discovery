import { Router } from 'express';
import * as c from '../controllers/predictionController.js';
import { validatePredictBody } from '../middleware/validation.js';

export default (db, ml) => {
  const r = Router();
  r.post('/', validatePredictBody, c.predict(db, ml));
  r.get('/history', c.history(db));
  r.get('/explain/:formula', c.explain(ml));
  return r;
};
