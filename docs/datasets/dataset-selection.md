# Dataset selection

## Current dataset: JARVIS-DFT dft_3d

Band gaps and stability come from the JARVIS-DFT `dft_3d` collection (NIST, via `jarvis-tools` and
figshare), 93,902 entries. Records are downloaded to `ml/data/raw/` (not committed) with a provenance
sidecar in `ml/data/metadata/dft_3d_source.json`.

- **Target:** OptB88vdW band gap (eV). Covers every entry. TBmBJ is more accurate but only ~23% of
  entries have it, so it would shrink the training set to about 21k rows.
- **Stability:** `ehull` (eV/atom above the convex hull), used by the stability layer and the
  `max_ehull` discovery constraint.
- **Caveat:** about 74% of training rows have a zero gap (metals). Metrics are dominated by them.

### Reproduce from scratch

```bash
python scripts/data/download_jarvis.py dft_3d     # -> ml/data/raw/dft_3d.json (~254 MB)
python scripts/data/to_csv.py dft_3d.json         # -> ml/data/processed/materials.csv, targets/, structures/
npm run setup                                     # preprocess -> train -> export -> seed SQLite
```

`preprocess` then writes two tables used by the engine:

- `ml/data/processed/band_gap_training.csv`: one row per unique formula, with the median band gap of
  its entries.
- `ml/data/processed/stability.csv`: one row per formula, with the lowest `ehull` of its entries (its
  most stable polymorph).

Pinned for reproducibility: `jarvis-tools==2026.6.12` (see `requirements.txt`).

Formation energy (eV/atom, all entries) and bulk modulus (GPa, the entries that have one) come from the same
file. `preprocess` writes them to `ml/data/processed/properties/`, and `ml/main.py train-property` trains a
model for each. Bulk moduli that are zero or negative are dropped.

## Materials Project labels (added to band-gap training)

`mp_3d.json` (Materials Project, 83,633 entries, PBE gaps) adds training rows for formulas JARVIS does not
contain: 25,287 formulas. Their PBE gap is mapped onto the JARVIS OptB88vdW scale with a linear fit on the
31,140 shared formulas (`ml/preprocessing/mp_augment.py`). The added rows join the training split and the
final fit only; the JARVIS test split is unchanged, and `band_gap_training.csv` stays JARVIS-only. The
median PBE gaps are cached in `ml/data/processed/mp_pbe_gaps.csv`. Evidence and costs are in
`docs/experiments/results.md`.

## OQMD (validation only)

`all_oqmd.json` (OQMD, 817,642 records, 450 MB unzipped) is used only to validate the band-gap model on
formulas absent from JARVIS and Materials Project. It is stored in `ml/data/raw/oqmd/`, is git-ignored, and is
not used for training. See `docs/experiments/results.md`.

## Synthetic demo (opt-in)

`scripts/data/generate_synthetic_dataset.py` writes about 2,500 charge-balanceable compositions with a
band gap from an electronegativity heuristic plus noise. **These are not measured or DFT values.** Use
it only to run the stack offline:

```bash
python ml/main.py generate-data
python ml/main.py preprocess --dataset synthetic
```

The UI shows a "Demo data" banner while a model trained on this set is active.

## Other candidate sources

Materials Project (already downloaded as `mp_3d`, not yet used for training), OQMD, AFLOW, and
Matbench sets for benchmarking. Each new source needs its own provenance sidecar and an entry in
`ml/preprocessing/`.
