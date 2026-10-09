# Sprint status (against the master plan)

| Sprint | Focus | State |
| --- | --- | --- |
| 0 | Research / problem definition | problem defined; literature review pending |
| 1 | Dataset | **done**: JARVIS dft_3d ingested, cleaned, and used for training |
| 2 | Representation | composition features done; structure features deferred |
| 3–4 | Baselines + evaluation | done (grouped split/CV, error analysis) |
| 5 | Prediction engine | done |
| 6 | Search | done (known + generated screening) |
| 7 | Candidate generation | element substitution done |
| 8 | Multi-objective | Pareto + score (2 objectives) |
| 9 | Validation | chemical, uncertainty, constraints, and stability (known materials; `max_ehull` constraint) done |
| 10 | Explainability | model-level and per-candidate explanations |
| 11–12 | Backend + DB | done; `node:sqlite` (no native build) |
| 13–17 | Frontend, explorer, discovery, candidates, charts | done (SVG charts); every page checked in a browser |
| 18 | Experiments | registry + page; runner writes JSON |
| 19 | Testing | pytest 53 · node:test 12 · vitest 5 |
| 20 | Reliability | input validation, timeouts, error handling; rate limiting/auth/backups pending |
| 21 | Integration | verified end-to-end (predict, discovery, UI) on the real model |
| 22–23 | Benchmarking, docs | docs refreshed for JARVIS; benchmark versioning pending |
