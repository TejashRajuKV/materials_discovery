# Feature plan

Status of the project today: JARVIS dft_3d band-gap pipeline, prediction, discovery with Pareto
ranking, SQLite seed, React UI. Gaps and options below are ordered by phase. Effort is a rough
size for one developer: S (≤1 day), M (≈1 week), L (several weeks).

Items marked **data ready** use fields already in `ml/data/processed/materials.csv` or
`ml/data/raw/dft_3d.json`, so they need no new downloads.

## Phase 1 — Make the existing product trustworthy (next)

| Item | Effort | Notes |
| --- | --- | --- |
| Stability filter on `ehull` | M | **Data ready.** Replace the `not_assessed` placeholder in `ml/validation/stability_validation.py`. Known materials have `ehull`; generated candidates do not (see decisions). Add `max_ehull` to the discovery spec. |
| Portable Python command | S | Make the ML interpreter configurable on Windows and Linux (`python3` vs `python`, `.venv` path). Fixes `npm run setup` and `test:ml` on a clean machine. |
| Browser check of every page | S | Load each page against the live API; fix what breaks. |
| Commit the work in logical pieces | S | Ingestion, ML wiring, backend SQLite change, docs. |
| Refresh stale docs | S | `results.md`, `dataset-selection.md`, `roadmap.md`, `agile-sprints.md`, `data-dictionary.md`. |
| CI on every push | S | GitHub Actions running `npm test` and `pytest`. Needs the data-free test path (already in place). |

## Phase 2 — Better science

**Status:** partly done. Done: zero-gap hurdle model, calibrated intervals, dimensionality and
crystal-system constraints. Not started: multi-property targets, structure descriptors, CFID, GNNs.
Reasons for the deferred items are given inline.


| Item | Effort | Notes |
| --- | --- | --- |
| Multi-property targets | L | **Not started.** Formation energy, bulk modulus, density, `ehull` as separate models. Adds objectives to the Pareto ranking. **Data ready.** Needs a `material_properties` table (already flagged in `schema.sql`) and a third objective, which changes the discovery spec and the ranking. |
| Zero-gap handling | M | **Done.** Hurdle model (metal classifier + non-metal regressor) selected by grouped CV: test MAE 0.235 eV vs 0.284 eV before. Trade-off: small-gap semiconductors (0–2 eV) are worse, and a semiconductor can be called metal. |
| Structure descriptors | M | **Not started, and blocked by design.** Structures exist only for known JARVIS entries. Generated compositions have no structure, so descriptors would not help screening until prototype-based generation (Phase 3) exists. |
| CFID features | M | **Not started.** Downloaded but unused. The join keys and coverage need checking first, since CFID is keyed to a 2021 subset. |
| Calibrated uncertainty | M | **Done.** Split-conformal intervals (90%) from out-of-fold residuals; held-out coverage 0.909. Intervals are constant width, not adaptive. Forest spread stays as the per-material signal. |
| Dimensionality and crystal-system constraints | S | **Done** for known materials (the most stable polymorph's attributes). Generated candidates fail when these are set, as with `max_ehull`. |
| Graph neural networks (CGCNN / MEGNet) | L | Trained on structures. Biggest accuracy lever, biggest cost. Roadmap V4. |

## Phase 3 — Smarter discovery

| Item | Effort | Notes |
| --- | --- | --- |
| Charge-balanced substitution | M | Only propose compositions that pass a charge-neutrality check, to cut invalid candidates. |
| Prototype-based generation | M | Reuse known crystal structures with new elements. Needs the structure descriptors. |
| Active learning loop | L | Pick the most informative candidates for DFT or experiment, then retrain. Needs a place to record results. |
| Adjustable Pareto weights | S | Let users change the trade-off in the UI and see the front move. The backend already computes it. |
| Saved searches and re-run alerts | M | Store a spec, re-run it after each model release, and show what changed. |

## Phase 4 — Data platform

| Item | Effort | Notes |
| --- | --- | --- |
| More sources | M each | Materials Project (already downloaded), OQMD, AFLOW, and experimental gaps for validation. |
| One-command refresh | M | Download, process, retrain, re-seed, and a diff of the results. |
| Data quality report page | M | Outliers, duplicates, and missing fields per dataset. |

## Phase 5 — User-facing features

| Item | Effort | Notes |
| --- | --- | --- |
| 3D structure viewer | M | Render each candidate's crystal with 3Dmol.js. Needs the structures already on disk. |
| Export | S | CSV and JSON for discovery results. PDF report for a single candidate later. |
| Model comparison page | S | Read the `models` table and show metrics side by side, plus error plots by gap range. |
| Periodic-table element picker | S | Replace typing element symbols with a clickable table. |

## Phase 6 — Operations and multi-user

| Item | Effort | Notes |
| --- | --- | --- |
| Resident ML service | M | Keep the model loaded instead of spawning Python per request. Fixes the 7 s predict latency and the 1.1 GB reload. Keeps the `pythonService.js` interface. |
| Smaller model | S | Prune or limit the forest. Changes the model, so it needs a metrics comparison first. |
| Job queue for discovery | M | Survive restarts and run jobs in parallel. |
| Auth and per-user history | L | Needed before anything is shared. |
| Automated database backups | S | Scheduled copies of `database/materials.db`. |

## Phase 7 — Research tooling

| Item | Effort | Notes |
| --- | --- | --- |
| Experiment tracking UI | M | Compare the runs in `experiments/` over time. Nothing reads them yet. |
| Versioned benchmark | S | Fixed held-out set, with results recorded per model release. |
| Literature and database links | S | Link candidates to Materials Project or ICSD entries where they exist. |

## Decisions needed before building

1. **Stability for generated candidates.** `ehull` exists only for known materials. Options: (a) apply the filter to known materials only and mark generated candidates "not assessed"; (b) train an `ehull` model and predict it for candidates, with its own uncertainty. (a) is quick and honest. (b) is more useful but a new model to validate.
2. **Which band-gap method to report.** Currently OptB88vdW. TBmBJ is more accurate but covers only about 23% of materials. A switch changes the dataset size.
3. **Scope of sharing.** Single-user local tool, or something other people will use? That decides when auth and job queues are needed.
4. **Deployment target.** Local only, or a hosted service? Hosting changes the Python, storage, and backup choices.

## Suggested order

Phase 1 in full, then multi-property targets and the zero-gap fix from Phase 2, then the resident ML service from Phase 6, since it makes everything else faster to test. The UI features in Phase 5 can run alongside any of these.
