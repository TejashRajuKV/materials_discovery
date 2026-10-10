import fs from 'node:fs';
import { Router } from 'express';
import { config } from '../config/config.js';
import { HttpError } from '../utils/helpers.js';

/** Cleaning report written by `preprocess`: what was dropped, merged, and what the target looks like. */
export default () => {
  const r = Router();
  r.get('/quality', (req, res) => {
    if (!fs.existsSync(config.preprocessReportPath)) {
      throw new HttpError(404, 'no preprocessing report yet; run `python ml/main.py preprocess`');
    }
    res.json(JSON.parse(fs.readFileSync(config.preprocessReportPath, 'utf8')));
  });
  return r;
};
