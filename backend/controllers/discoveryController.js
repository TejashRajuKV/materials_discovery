import * as service from '../services/discoveryService.js';
import { HttpError, toInt } from '../utils/helpers.js';

const idParam = (req) => {
  const id = toInt(req.params.id, NaN);
  if (Number.isNaN(id)) throw new HttpError(400, 'id must be an integer');
  return id;
};

export const create = (db, ml) => (req, res) => {
  const { spec, generate, include_known: includeKnown } = req.body;
  const { job } = service.startJob(db, ml, spec, {
    generate: generate !== false,
    include_known: includeKnown !== false,
  });
  res.status(202).json(job);
};

export const list = (db) => (req, res) => res.json(service.listJobs(db));
export const get = (db) => (req, res) => res.json(service.getJobWithCandidates(db, idParam(req)));

const CSV_COLUMNS = ['origin', 'rank', 'formula', 'pareto_rank', 'score', 'prediction', 'uncertainty', 'confidence',
  'validation', 'properties'];

const csvCell = (value) => {
  if (value === null || value === undefined) return '';
  const text = typeof value === 'object' ? JSON.stringify(value) : String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
};

/** One row per candidate: origin, rank, formula, scores, prediction, validation status, property values. */
export const exportCsv = (db) => (req, res) => {
  const job = service.getJobWithCandidates(db, idParam(req));
  const rows = [...job.known_matches, ...job.novel_candidates].map((c) => ({
    ...c, validation: c.validation?.overall ?? '',
  }));
  const lines = [CSV_COLUMNS.join(','), ...rows.map((r) => CSV_COLUMNS.map((k) => csvCell(r[k])).join(','))];
  res.type('text/csv').attachment(`discovery-${job.id}.csv`).send(lines.join('\n') + '\n');
};
