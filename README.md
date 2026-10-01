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
pip install -r requirements.txt
npm run setup          # synthetic data -> preprocess -> train -> export -> seed SQLite
npm run dev:backend    # API on :3000
npm run dev:frontend   # UI on :5173
npm test               # backend + frontend + ML tests
```

The ML engine is a CLI (`python ml/main.py ...`) that the backend runs as a subprocess; there is no
separate ML server. See `docs/development/setup.md` for environment variables and troubleshooting.

## What it does

Pick band-gap requirements (range, target, element rules, max uncertainty) → the engine screens known
materials plus substitution-generated compositions → predicts band gap with uncertainty → validates
→ ranks the trade-off between hitting the target and model certainty (Pareto front) → explains the
top candidates.

> **Status: demo data.** No real dataset could be downloaded where this was built, so the model is
> trained on a *synthetic* band-gap set and the UI says so. Metrics and candidates illustrate the
> workflow only — see `docs/datasets/dataset-selection.md` for how to swap in real data.

## Documentation

- `docs/architecture/` — system, backend, ML, and database design
- `docs/research/` — background, literature review, problem definition, methodology
- `docs/datasets/` — dataset selection, analysis, data dictionary
- `docs/experiments/` — experiment protocol and results
- `docs/development/` — roadmap, sprint plan, setup guide

## License

MIT — see [LICENSE](LICENSE).
