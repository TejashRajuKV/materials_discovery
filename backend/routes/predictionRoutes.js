import { Router } from 'express';
import * as c from '../controllers/predictionController.js';
import { validatePredictBody } from '../middleware/validation.js';

export default (db, ml, { limitPredict }) => {
  const r = Router();
  r.post('/', limitPredict, validatePredictBody, c.predict(db, ml));
  r.get('/history', c.history(db));
  r.get('/explain/:formula', c.explain(ml));
  return r;
};
