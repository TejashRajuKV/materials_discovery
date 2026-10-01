# Problem definition

**One initial discovery problem:** given a target *electronic property* — the band gap (eV) — find
candidate inorganic compositions that satisfy user-defined requirements, and say how certain we are.

> A computational materials-discovery system in which ML models learn composition → property
> relationships and are combined with candidate generation, multi-objective ranking, uncertainty
> estimation and layered validation to surface promising materials for stated requirements.

The React/Express/SQLite application is the platform around that research, not the research itself.

## Scope of the first version (MVP → V2 slice)
In: composition-only representation, band-gap prediction, search over known + generated
compositions, Pareto ranking (target distance vs. uncertainty), chemical validation, model-level
explanations, a web UI.
Out (documented future work): crystal-structure/graph models, multiple properties, thermodynamic
stability, active learning, generative models, authentication.

## Success criteria
1. Beats a mean-predictor baseline on a **chemical-system-grouped** held-out split.
2. Reports uncertainty that correlates with error.
3. Discovery results always show which layers of validation were *not* assessed.
4. Every experiment is reproducible from a recorded dataset hash and seed.
