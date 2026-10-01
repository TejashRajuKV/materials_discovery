import { HttpError } from '../utils/helpers.js';
import { config } from '../config/config.js';

const FORMULA_RE = /^[A-Za-z0-9().\s]{1,60}$/;

export function validatePredictBody(req, res, next) {
  const { formulas } = req.body ?? {};
  if (!Array.isArray(formulas) || formulas.length === 0) {
    return next(new HttpError(400, '`formulas` must be a non-empty array of strings'));
  }
  if (formulas.length > config.maxFormulasPerRequest) {
    return next(new HttpError(400, `at most ${config.maxFormulasPerRequest} formulas per request`));
  }
  if (!formulas.every((f) => typeof f === 'string' && FORMULA_RE.test(f.trim()))) {
    return next(new HttpError(400, 'each formula must be a string of letters, digits, parentheses and dots (max 60 chars)'));
  }
  req.body.formulas = formulas.map((f) => f.trim());
  next();
}

export function validateDiscoveryBody(req, res, next) {
  const { spec } = req.body ?? {};
  if (!spec || typeof spec !== 'object' || Array.isArray(spec)) {
    return next(new HttpError(400, '`spec` must be an object describing the requirements'));
  }
  const bad = [...(spec.include_elements ?? []), ...(spec.exclude_elements ?? [])]
    .some((e) => typeof e !== 'string' || !/^[A-Z][a-z]?$/.test(e));
  if (bad) return next(new HttpError(400, 'element lists must contain element symbols such as "Fe"'));

  const band = spec.band_gap ?? {};
  const given = ['min', 'max', 'target'].filter((k) => band[k] !== undefined && band[k] !== '' && band[k] !== null);
  if (given.some((k) => !Number.isFinite(Number(band[k])))) {
    return next(new HttpError(400, 'band_gap min/max/target must be numbers'));
  }
  if (given.includes('min') && given.includes('max') && Number(band.min) > Number(band.max)) {
    return next(new HttpError(400, 'band_gap.min must not exceed band_gap.max'));
  }
  const hasElementRule = spec.include_elements?.length || spec.exclude_elements?.length || spec.max_elements;
  if (!given.length && !hasElementRule) {
    return next(new HttpError(400, 'specify at least one requirement (band gap range/target or an element rule)'));
  }
  next();
}
