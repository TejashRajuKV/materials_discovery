# Database (SQLite, `backend/database/schema.sql`)

`materials` (formula unique, band_gap, source, predicted_band_gap, uncertainty) ·
`models` (version unique, target, algorithm, metrics JSON, details JSON) ·
`experiments` (→ models) · `predictions` (log) · `discovery_jobs` (spec JSON, status
`running|completed|failed`, stats JSON, error) · `candidates` (→ jobs, cascade; origin
`known|generated`, rank, pareto_rank, score, prediction, uncertainty, validation JSON, explanation JSON).

The proposed generic `material_properties` table is deferred until a second property exists.
`database/materials.db` is git-ignored; recreate with `npm run setup`. WAL mode, foreign keys on.
`database/backups/` is reserved for backups (not automated yet).
