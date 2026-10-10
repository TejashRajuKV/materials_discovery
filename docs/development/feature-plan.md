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
crystal-system constraints, formation-energy and bulk-modulus models. Not started: a third Pareto objective,
structure descriptors, CFID, GNNs.
Reasons for the deferred items are given inline.


| Item | Effort | Notes |
| --- | --- | --- |
| Multi-property targets | L | **Partly done.** Formation energy and bulk modulus have models, a `material_properties` table, prediction and constraints. **Not done:** density (not modelled yet), and a third Pareto objective, which changes the ranking. |
| Zero-gap handling | M | **Done.** Hurdle model (metal classifier + non-metal regressor) selected by grouped CV: test MAE 0.235 eV vs 0.284 eV before (0.248 eV after the smaller forests, see Smaller model). Trade-off: small-gap semiconductors (0–2 eV) are worse, and a semiconductor can be called metal. |
| Structure descriptors | M | **Not started, and blocked by design.** Structures exist only for known JARVIS entries. Generated compositions have no structure, so descriptors would not help screening until prototype-based generation (Phase 3) exists. |
| CFID features | M | **Not started.** Downloaded but unused. The join keys and coverage need checking first, since CFID is keyed to a 2021 subset. |
| Calibrated uncertainty | M | **Done.** Split-conformal intervals (90%) from out-of-fold residuals; held-out coverage 0.909. Intervals are constant width, not adaptive. Forest spread stays as the per-material signal. |
| Dimensionality and crystal-system constraints | S | **Done** for known materials (the most stable polymorph's attributes). Generated candidates fail when these are set, as with `max_ehull`. |
| Graph neural networks (CGCNN / MEGNet) | L | Trained on structures. Biggest accuracy lever, biggest cost. Roadmap V4. |

## Phase 3 — Smarter discovery

| Item | Effort | Notes |
| --- | --- | --- |
| Charge-balanced substitution | M | **Done.** Anion-containing candidates must balance their charges; intermetallics are not checked. About 81% of anion candidates pass. Results are cached on disk, since the check takes about 30 ms per composition. |
| Prototype-based generation | M | Reuse known crystal structures with new elements. Needs the structure descriptors. |
| Active learning loop | L | Pick the most informative candidates for DFT or experiment, then retrain. Needs a place to record results. |
| Adjustable Pareto weights | S | **Done** for the within-front score (`weights` in the spec, and in the form). The front itself does not depend on the weights. |
| Saved searches and re-run alerts | M | **Partly done.** Save a spec under a name and re-run it on the Discovery page. Alerts and automatic re-runs after a model release are not done. |

## Phase 4 — Data platform

**Status: not started.** Materials Project is downloaded but not used. Each new source needs a provenance file and a loader.

| Item | Effort | Notes |
| --- | --- | --- |
| More sources | M each | **Not started.** Materials Project (already downloaded), OQMD, AFLOW, and experimental gaps for validation. |
| One-command refresh | M | Download, process, retrain, re-seed, and a diff of the results. |
| Data quality report page | M | **Done** (`/data`): what preprocessing dropped and merged, and the target's shape. Missing-field counts per source are not shown yet. |

## Phase 5 — User-facing features

**Status: partly done.** CSV export and the model comparison page (Models) are done. Structure viewer and periodic-table picker are not started.

| Item | Effort | Notes |
| --- | --- | --- |
| 3D structure viewer | M | **Done** for known materials, as an SVG unit-cell viewer with drag to rotate (no new dependency). Generated candidates have no structure. |
| Export | S | **CSV done** for discovery results (`/api/discovery/:id/export.csv`). JSON and a per-candidate PDF are not done. |
| Model comparison page | S | Read the `models` table and show metrics side by side, plus error plots by gap range. |
| Periodic-table element picker | S | **Done** in the discovery form: click to require, click again to exclude. |

## Phase 6 — Operations and multi-user

**Status: partly done.** Resident service, backup script, and the faster Pareto ranking are done. Auth, a job queue, and a smaller band-gap model are not. Auth and hosting need your decisions.

| Item | Effort | Notes |
| --- | --- | --- |
| Resident ML service | M | **Done** (`ml/service.py`, opt-in with `ML_SERVICE_URL`). Predict is about 0.5 s warm, against 6–7 s. The 1.2 GB band-gap model is still large in memory. |
| Smaller model | S | **Done.** Band-gap forests use minimum leaf 5 (was 1). Bundle 0.35 GB (was 1.24 GB). Held-out MAE 0.248 eV (was 0.235). The property models already used smaller forests. |
| Job queue for discovery | M | **Partly done.** Jobs left running by a stopped server are marked failed at startup. Jobs still run in-process, not from a queue. |
| Auth and per-user history | L | Needed before anything is shared. |
| Automated database backups | S | **Done as a script** (`scripts/backup-db.js`, with retention). Scheduling it is left to the host. |

## Phase 7 — Research tooling

**Status: not started.** The Experiments page already lists runs; comparison over time and a versioned benchmark are not done.

| Item | Effort | Notes |
| --- | --- | --- |
| Experiment tracking UI | M | **Not done.** Only one run exists, so there is nothing to compare yet. |
| Versioned benchmark | S | Fixed held-out set, with results recorded per model release. |
| Literature and database links | S | **Partly done**: a literature search link on material details. Materials Project and ICSD links need the exact identifiers and URL formats checked first. |

## Decisions needed before building

1. **Stability for generated candidates.** `ehull` exists only for known materials. Options: (a) apply the filter to known materials only and mark generated candidates "not assessed"; (b) train an `ehull` model and predict it for candidates, with its own uncertainty. (a) is quick and honest. (b) is more useful but a new model to validate.
2. **Which band-gap method to report.** Currently OptB88vdW. TBmBJ is more accurate but covers only about 23% of materials. A switch changes the dataset size.
3. **Scope of sharing.** Single-user local tool, or something other people will use? That decides when auth and job queues are needed.
4. **Deployment target.** Local only, or a hosted service? Hosting changes the Python, storage, and backup choices.

## Suggested order

Phase 1 in full, then multi-property targets and the zero-gap fix from Phase 2, then the resident ML service from Phase 6, since it makes everything else faster to test. The UI features in Phase 5 can run alongside any of these.
