# Roadmap

| Version | Content | Status |
| --- | --- | --- |
| MVP | dataset → features → ML prediction → search → ranking → React dashboard | **built** (on synthetic data) |
| V2 | uncertainty, Pareto ranking, explanations, experiments page | **built** (single property) |
| V3 | candidate generation, layered validation, experiment tracking | **partly built** (substitution generation; stability layer is a placeholder) |
| V4 | structure/graph models, active learning, generative design, multi-property optimisation | not started |

## Immediate next steps
1. **Real dataset** (see `datasets/dataset-selection.md`) and rewrite analysis/results docs.
2. Literature review (`research/literature-review.md`).
3. Stability data → implement `ml/validation/stability_validation.py`.
4. Multiple target properties (adds a third objective and `material_properties` table).
5. Long-lived ML service, authentication. (Done: calibrated intervals, rate limiting, backups, CI.)
