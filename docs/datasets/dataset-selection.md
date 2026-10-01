# Dataset selection

**Required format** (`ml/data/raw/<file>.csv`): columns `formula`, `band_gap` (eV); optional `source`.

## Current dataset: synthetic demo (placeholder)
`scripts/data/generate_synthetic_dataset.py` writes ~2,500 charge-balanceable compositions with a
band gap from an electronegativity/ionicity heuristic plus noise. **These are not measured or DFT
values.** It exists so the whole stack runs offline; the UI shows a banner while it is in use.
Metrics on it measure how well the model recovers the heuristic, *not* real-world accuracy.

## Chosen real dataset: JARVIS-DFT `dft_3d`
Structures + DFT properties for ~76k 3D materials (about 55–60k have an OptB88vdW gap). Fetch it on a machine
that can reach figshare (the build sandbox's proxy returns 403 for `ndownloader.figshare.com`):

```bash
pip install jarvis-tools
python scripts/data/download_jarvis.py                        # -> ml/data/raw/jarvis_dft_3d.csv
python ml/main.py bootstrap --file ml/data/raw/jarvis_dft_3d.csv && npm run db:seed
```

Notes: `--target mbj_bandgap` gives a more accurate gap but far fewer rows; OptB88vdW (GGA) systematically
underestimates gaps. JARVIS has many polymorphs per formula — the cleaner merges them by median, and the grouped
split keeps a chemical system on one side of the split. The CSV also carries `jid`, `formation_energy_peratom` and
`ehull`, which the future stability-validation layer should use. `--with-structures` saves the atoms for later
structure-based models. Other JARVIS sets (`cfid_3d`, `dft_3d_2021`) use the same schema; `oqmd_3d`/`mp_3d` are for
later cross-database validation.

## Replacing it with any other data
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
