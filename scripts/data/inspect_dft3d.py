"""Sprint 2 inspection: field inventory and target analysis for dft_3d.

Read-only. Reports what is in the raw file so schema decisions are made
from evidence rather than assumption.
"""

import json
from collections import Counter
from pathlib import Path

import numpy as np

RAW = Path(__file__).resolve().parents[2] / "ml" / "data" / "raw" / "dft_3d.json"
MISSING_SENTINELS = {None, "", "na", "n/a", "none", "nan", "null", "-"}


def load():
    with RAW.open(encoding="utf-8") as handle:
        return json.load(handle)


def numeric(values):
    """Coerce to float array, mapping every non-numeric sentinel to NaN."""
    out = np.full(len(values), np.nan)
    for i, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        out[i] = float(value)
    return out


def describe(name, arr):
    finite = arr[np.isfinite(arr)]
    print(f"--- {name} (n={finite.size}) ---")
    print(f"  min    {finite.min():.4f}")
    print(f"  p25    {np.percentile(finite, 25):.4f}")
    print(f"  median {np.median(finite):.4f}")
    print(f"  p75    {np.percentile(finite, 75):.4f}")
    print(f"  max    {finite.max():.4f}")
    print(f"  mean   {finite.mean():.4f}")
    print(f"  exactly 0.0 : {int((finite == 0).sum())} ({100 * (finite == 0).mean():.1f}%)")
    print(f"  negatives   : {int((finite < 0).sum())}")
    print()


def main():
    records = load()
    n = len(records)
    print(f"=== DATASET ===\nrecords: {n}\nfields:  {len(records[0])}\n")

    print("=== SENTINEL FORMS PER FIELD (top-level only) ===")
    for field in ("mbj_bandgap", "ehull", "hse_gap", "icsd", "dimensionality"):
        kinds = Counter(type(r.get(field)).__name__ for r in records)
        sample = [r.get(field) for r in records[:5]]
        print(f"  {field:<16} {dict(kinds)}  sample={sample}")
    print()

    print("=== TARGET AVAILABILITY ===")
    mbj = numeric([r.get("mbj_bandgap") for r in records])
    opt = numeric([r.get("optb88vdw_bandgap") for r in records])
    for name, arr in (("mbj_bandgap (TBmBJ)", mbj), ("optb88vdw_bandgap", opt)):
        valid = int(np.isfinite(arr).sum())
        print(f"  {name:<24} valid: {valid:>6}  ({100 * valid / n:.1f}%)")
    both = int((np.isfinite(mbj) & np.isfinite(opt)).sum())
    print(f"  {'both valid':<24}       {both:>6}  ({100 * both / n:.1f}%)")
    print()

    describe("mbj_bandgap (TBmBJ)", mbj)
    describe("optb88vdw_bandgap", opt)

    labelled = [r for r in records if isinstance(r.get("mbj_bandgap"), (int, float))]
    print(f"=== TBmBJ SUBSET (n={len(labelled)}) ===")
    print("  dimensionality:", Counter(r.get("dimensionality") for r in labelled).most_common())
    print("  func          :", Counter(r.get("func") for r in labelled).most_common(3))
    print()

    ehull = np.array([r.get("ehull", np.nan) for r in labelled], dtype=float)
    print("=== STABILITY OF LABELLED SUBSET (ehull, eV/atom) ===")
    for label, mask in (("== 0", ehull == 0), ("< 0.025 (stable)", ehull < 0.025), ("> 0.1 (unstable)", ehull > 0.1)):
        print(f"  {label:<18} {int(mask.sum()):>6}  ({100 * mask.mean():.1f}%)")
    print()

    gaps = mbj[np.isfinite(mbj)]
    semiconducting = gaps > 0
    print("=== CLASS IMBALANCE (TBmBJ) ===")
    print(f"  metals (gap == 0)     : {int((gaps == 0).sum()):>6}  ({100 * (gaps == 0).mean():.1f}%)")
    print(f"  semiconductors        : {int(semiconducting.sum()):>6}  ({100 * semiconducting.mean():.1f}%)")
    window = ((gaps > 1) & (gaps < 5)).sum()
    print(f"  semiconductors 1-5 eV : {int(window):>6}  ({100 * window / semiconducting.sum():.1f}% of semiconductors)")
    print()

    print("=== IDENTITY AND DUPLICATION ===")
    jids = [r.get("jid") for r in records]
    formulas = [r.get("formula") for r in records]
    print(f"  unique jid            : {len(set(jids))} / {n}")
    print(f"  unique formula        : {len(set(formulas))} / {n}")
    print(f"  polymorph extra rows  : {len(formulas) - len(set(formulas))}")
    counts = Counter(r.get("formula") for r in labelled)
    repeated = sum(v for v in counts.values() if v > 1)
    print(f"  labelled rows sharing a formula with another labelled row: {repeated} ({100 * repeated / len(labelled):.1f}%)")
    print(f"  max records per formula: {max(counts.values())}")
    print()

    print("=== NAIVE BASELINE (predict the mean) ===")
    print(f"  constant {gaps.mean():.4f} eV  ->  MAE {np.abs(gaps - gaps.mean()).mean():.4f} eV  (target std {gaps.std():.4f})")


if __name__ == "__main__":
    main()
