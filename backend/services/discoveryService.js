import { logger } from '../utils/logger.js';
import { HttpError, parseJson } from '../utils/helpers.js';

const jobView = (row) => row && { ...row, spec: parseJson(row.spec), stats: parseJson(row.stats) };

const candidateView = (row) => ({
  ...row,
  validation: parseJson(row.validation),
  explanation: parseJson(row.explanation),
});

/** Create a job and run the ML pipeline in the background. Returns the job immediately. */
export function startJob(db, ml, spec, options = {}) {
  const { lastInsertRowid: id } = db.prepare("INSERT INTO discovery_jobs (spec, status) VALUES (?, 'running')")
    .run(JSON.stringify(spec));

  const run = ml.discover({ spec, ...options })
    .then((result) => saveResult(db, id, result))
    .catch((err) => {
      logger.warn(`discovery job ${id} failed: ${err.message}`);
      db.prepare("UPDATE discovery_jobs SET status = 'failed', error = ?, completed_at = datetime('now') WHERE id = ?")
        .run(err.message, id);
    });
  return { job: getJob(db, id), done: run };
}

function saveResult(db, id, result) {
  const insert = db.prepare(`INSERT INTO candidates
    (job_id, formula, origin, rank, pareto_rank, score, prediction, uncertainty, confidence, validation, explanation)
    VALUES (@job_id, @formula, @origin, @rank, @pareto_rank, @score, @prediction, @uncertainty, @confidence, @validation, @explanation)`);
  db.transaction(() => {
    for (const c of [...result.known_matches, ...result.novel_candidates]) {
      insert.run({
        job_id: id, formula: c.formula, origin: c.origin, rank: c.rank, pareto_rank: c.pareto_rank,
        score: c.score, prediction: c.prediction, uncertainty: c.uncertainty, confidence: c.confidence,
        validation: JSON.stringify(c.validation), explanation: c.explanation ? JSON.stringify(c.explanation) : null,
      });
    }
    db.prepare(`UPDATE discovery_jobs SET status = 'completed', stats = ?, spec = ?, model_version = ?,
      completed_at = datetime('now') WHERE id = ?`)
      .run(JSON.stringify(result.stats), JSON.stringify(result.spec), result.model_version, id);
  })();
}

export function getJob(db, id) {
  return jobView(db.prepare('SELECT * FROM discovery_jobs WHERE id = ?').get(id));
}

export function listJobs(db) {
  return db.prepare('SELECT * FROM discovery_jobs ORDER BY id DESC LIMIT 50').all().map(jobView);
}

export function getJobWithCandidates(db, id) {
  const job = getJob(db, id);
  if (!job) throw new HttpError(404, `discovery job ${id} not found`);
  const rows = db.prepare('SELECT * FROM candidates WHERE job_id = ? ORDER BY origin, rank').all(id).map(candidateView);
  return {
    ...job,
    known_matches: rows.filter((r) => r.origin === 'known'),
    novel_candidates: rows.filter((r) => r.origin === 'generated'),
  };
}

export function getCandidate(db, id) {
  const row = db.prepare('SELECT * FROM candidates WHERE id = ?').get(id);
  if (!row) throw new HttpError(404, `candidate ${id} not found`);
  return candidateView(row);
}

export function compareCandidates(db, ids) {
  const rows = ids.map((id) => getCandidate(db, id));
  return rows;
}
