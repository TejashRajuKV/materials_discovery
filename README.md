# AI Materials Discovery

Machine-learning platform for screening, predicting, and optimising materials.

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | React (Vite), JavaScript, CSS |
| Backend | Node.js, Express.js |
| ML engine | Python |
| Database | SQLite |

The frontend, backend, and ML engine are separate processes that talk over
HTTP, so each layer can be developed and tested independently.

## Layout

```
frontend/   React UI: pages, components, services, hooks, styles
backend/    Express API: routes, controllers, services, SQLite access
ml/         Python ML: preprocessing, models, discovery, validation, evaluation
database/   Local SQLite database and backups
experiments/Research experiment folders and results
tests/      Frontend, backend, ML, and integration tests
scripts/    Setup, data, training, and maintenance scripts
docs/       Research, architecture, dataset, experiment, and dev docs
```

## Getting started

```bash
npm install
npm run dev:backend     # API on :3000
npm run dev:frontend    # UI on :5173
python ml/main.py       # ML service on :8000
```

Configuration lives in `.env` (copy of the committed defaults, git-ignored).

## Documentation

- `docs/architecture/` — system, backend, ML, and database design
- `docs/research/` — background, literature review, problem definition, methodology
- `docs/datasets/` — dataset selection, analysis, data dictionary
- `docs/experiments/` — experiment protocol and results
- `docs/development/` — roadmap, sprint plan, setup guide

## License

MIT — see [LICENSE](LICENSE).
