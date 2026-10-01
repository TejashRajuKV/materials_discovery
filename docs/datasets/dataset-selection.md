# Dataset selection

**Required format** (`ml/data/raw/<file>.csv`): columns `formula`, `band_gap` (eV); optional `source`.

## Current dataset: synthetic demo (placeholder)
`scripts/data/generate_synthetic_dataset.py` writes ~2,500 charge-balanceable compositions with a
band gap from an electronegativity/ionicity heuristic plus noise. **These are not measured or DFT
values.** It exists so the whole stack runs offline; the UI shows a banner while it is in use.
Metrics on it measure how well the model recovers the heuristic, *not* real-world accuracy.

## Replacing it with real data (next step)
Candidates: Matbench `matbench_mp_gap` / `matbench_expt_gap`, Materials Project band gaps
(API key), JARVIS-DFT, OQMD. Download is blocked in the build sandbox (figshare, Zenodo and the
Materials Project API were unreachable), so this must be done on a networked machine:

1. Save as `ml/data/raw/<name>.csv` with `formula,band_gap,source`.
2. Set `RAW_DEFAULT_FILE` in `ml/config.py` (or add a CLI flag), then `npm run setup`.
3. Re-read `docs/datasets/dataset-analysis.md` and rewrite it for the new data.
