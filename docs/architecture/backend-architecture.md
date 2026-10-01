# Backend (`backend/`)

Layers: `routes → controllers → services → (SQLite | pythonService)`; `createApp({db, ml})` takes
both as arguments so tests use an in-memory DB and a fake ML engine.

| Method & path | Purpose |
| --- | --- |
| `GET /api/health` | liveness |
| `GET /api/materials?q&min_gap&max_gap&sort&limit&offset` | search/filter/paginate |
| `GET /api/materials/stats` · `/:id` | dataset summary + histogram · one material |
| `POST /api/predict` `{formulas:[…]}` | predictions (+ recorded value if known); logged |
| `GET /api/predict/history` · `/explain/:formula` | recent predictions · model-level explanation |
| `POST /api/discovery` `{spec}` → 202 | start a job; `GET /api/discovery`, `/:id` (with candidates) |
| `GET /api/candidates/:id` · `/compare?ids=1,2` | candidate detail · side-by-side |
| `GET /api/models` · `/models/:id` · `/experiments` | registered models and experiments |

Hardening: security headers; per-IP fixed-window rate limits on `POST /api/predict` (60/min) and
`POST /api/discovery` (10/min) → `429` + `Retry-After`; at most 2 concurrent discovery jobs (`429`); jobs left
`running` by a dead process are marked `failed` at startup; online SQLite backups via `npm run db:backup`.
The rate limiter is in-memory (single process) — use a shared store or reverse proxy if scaled out.

Input is validated in `middleware/validation.js` (formula charset/length/count, spec ranges,
element symbols) and again by the ML engine. Errors are JSON `{error, details?}`.
There is no authentication in the MVP.
