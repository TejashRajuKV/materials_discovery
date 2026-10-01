import * as service from '../services/predictionService.js';

export const predict = (db, ml) => async (req, res) => {
  res.json({ predictions: await service.predict(db, ml, req.body.formulas) });
};

export const history = (db) => (req, res) => res.json(service.recentPredictions(db));

export const explain = (ml) => async (req, res) => res.json(await ml.explain(req.params.formula));
