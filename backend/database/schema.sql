-- One row per known material. Only band gap exists in the MVP; add a
-- material_properties table when a second target property is introduced.
CREATE TABLE IF NOT EXISTS materials (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  formula             TEXT NOT NULL UNIQUE,
  band_gap            REAL,
  source              TEXT,
  predicted_band_gap  REAL,
  uncertainty         REAL,
  created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_materials_band_gap ON materials (band_gap);

CREATE TABLE IF NOT EXISTS models (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  name             TEXT NOT NULL,
  version          TEXT NOT NULL UNIQUE,
  target_property  TEXT NOT NULL,
  algorithm        TEXT NOT NULL,
  metrics          TEXT NOT NULL,   -- JSON: per-model cv/test metrics
  details          TEXT NOT NULL,   -- JSON: dataset, error analysis, importances, uncertainty
  created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiments (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT NOT NULL,
  model_id    INTEGER REFERENCES models(id),
  dataset     TEXT,
  metrics     TEXT NOT NULL,        -- JSON
  notes       TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS predictions (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  model_version TEXT,
  formula      TEXT NOT NULL,
  prediction   REAL NOT NULL,
  uncertainty  REAL NOT NULL,
  confidence   TEXT,
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS discovery_jobs (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  spec          TEXT NOT NULL,      -- JSON requirements
  status        TEXT NOT NULL CHECK (status IN ('running','completed','failed')),
  stats         TEXT,               -- JSON
  error         TEXT,
  model_version TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  completed_at  TEXT
);

CREATE TABLE IF NOT EXISTS candidates (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id       INTEGER NOT NULL REFERENCES discovery_jobs(id) ON DELETE CASCADE,
  formula      TEXT NOT NULL,
  origin       TEXT NOT NULL CHECK (origin IN ('known','generated')),
  rank         INTEGER NOT NULL,
  pareto_rank  INTEGER NOT NULL,
  score        REAL NOT NULL,
  prediction   REAL NOT NULL,
  uncertainty  REAL NOT NULL,
  confidence   TEXT,
  validation   TEXT,                -- JSON
  explanation  TEXT                 -- JSON, top candidates only
);
CREATE INDEX IF NOT EXISTS idx_candidates_job ON candidates (job_id, origin, rank);
