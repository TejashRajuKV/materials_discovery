# Roadmap

| Version | Content | Status |
| --- | --- | --- |
| MVP | dataset → features → ML prediction → search → ranking → React dashboard | **built** (JARVIS dft_3d) |
| V2 | uncertainty, Pareto ranking, explanations, experiments page | **built** (single property) |
| V3 | candidate generation, layered validation, experiment tracking | **partly built**: substitution generation and stability filter for known materials are done; generated candidates have no stability data |
| V4 | structure/graph models, active learning, generative design, multi-property optimisation | not started |

The per-item plan, with effort and dependencies, is in [feature-plan.md](feature-plan.md).

## Done in Phase 1
- Real dataset: JARVIS dft_3d, wired into preprocessing, training, discovery, and the database.
- Stability layer on `ehull` for known materials, plus the `max_ehull` discovery constraint.
- Portable Python resolution (`.venv`, `PYTHON_BIN`) for the backend and npm scripts.
- Browser check of every page, and a fix for the discovery form's number-input step.

## Done in Phase 2
- Zero-gap hurdle model, selected by grouped CV (held-out MAE 0.235 eV, from 0.284 eV).
- Split-conformal 90% intervals on predictions; held-out coverage 0.909.
- Dimensionality and crystal-system constraints for known materials.
- Formation-energy and bulk-modulus models (random forest, 90% intervals), stored in `material_properties`.
  Property ranges are discovery constraints; generated candidates get predicted values, so they can pass them.
- The feature plan lists what is deferred and why: structure descriptors, CFID, the third objective.

## Next
1. A third Pareto objective from formation energy or bulk modulus, and density as another property.
2. Prototype-based generation, which makes structure descriptors useful for screening.
3. Long-lived ML service, to remove the per-request Python start and the 1.1 GB model reload.
4. Calibrated uncertainty (conformal intervals) to replace raw forest spread.
5. Auth, job queue, and database backups before anything is shared.
