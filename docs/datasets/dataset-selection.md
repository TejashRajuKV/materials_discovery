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

1. Download a band-gap dataset as CSV/TSV/JSON (target in **eV**). Matbench `matbench_expt_gap` /
   `matbench_mp_gap` (via `matminer.datasets.load_dataset(...).to_csv(...)`), Materials Project, JARVIS and OQMD
   exports all work.
2. Put it in `ml/data/raw/` (or anywhere) and run

   ```bash
   python3 ml/main.py bootstrap --file ml/data/raw/mydata.csv      # preprocess -> train -> export
   npm run db:seed                                                  # replaces the materials table
   ```

   The formula and band-gap columns are auto-detected (`formula`, `pretty_formula`, `composition`, …;
   `band_gap`, `gap expt`, `Eg`, `gap`, …) or set with `--formula-col` / `--target-col`. A `structure`
   column of pymatgen dicts (Matbench) is reduced to a formula. A `source` column is kept; otherwise the
   file name is the source, which also removes the synthetic-data banner in the UI.
3. Restart nothing — the API reads the new DB. Delete old discovery jobs if you want a clean slate
   (`rm database/materials.db && npm run db:seed`).
4. Rewrite `docs/datasets/dataset-analysis.md` and `docs/experiments/results.md` for the new data.

Size guide (measured on the synthetic set, 8 cores): 2.5k rows ≈ 30 s to bootstrap; 30k rows ≈ 4 min;
discovery over 30k known materials ≈ 15 s. Real datasets of 100k+ rows will take proportionally longer
to train; the backend allows discovery 120 s (`ML_TIMEOUT_MS`).
