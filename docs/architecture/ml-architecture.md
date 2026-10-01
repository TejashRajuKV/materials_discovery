# ML architecture (`ml/`)

| Package | Role |
| --- | --- |
| `preprocessing/` | clean → validate → processed CSV + report |
| `representation/` | formula → pymatgen `Composition` → 63 Magpie-style features (structure features: future) |
| `training/` | grouped split/CV, baselines, optional RF tuning, bundle save (`ml/models/saved/band_gap/`) |
| `evaluation/` | metrics, error analysis by gap range & anion class, benchmark table |
| `prediction/` | validate → featurize → predict → RF tree-spread uncertainty |
| `discovery/` | substitution generation, constraint filtering, end-to-end `run_discovery` |
| `optimization/` | constraints, objectives, non-dominated sorting, ranking |
| `validation/` | chemical (parse, elements, charge balance), stability (**not assessed**), uncertainty, constraints |
| `explainability/` | global importances; per-prediction top features + nearest known materials |
| `experiments/` | named experiment runs written to `experiments/<id>/` |

CLI: `python ml/main.py {bootstrap|generate-data|preprocess|train [--tune]|export|predict|discover|explain}`.
Run as `python ml/main.py` or `python -m ml.main` from the repo root.
