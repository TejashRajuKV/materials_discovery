"""Download a JARVIS-DFT dataset (default: dft_3d) and convert it to the project's raw CSV.

Run this on a machine that can reach figshare (the build sandbox's proxy blocks it):

    pip install jarvis-tools
    python scripts/data/download_jarvis.py                      # OptB88vdW gap -> ml/data/raw/jarvis_dft_3d.csv
    python scripts/data/download_jarvis.py --target mbj_bandgap # more accurate gap, far fewer rows
    python scripts/data/download_jarvis.py --with-structures    # also save atoms for future structure models
    python ml/main.py bootstrap --file ml/data/raw/jarvis_dft_3d.csv && npm run db:seed

Output columns: formula, band_gap (eV), source, jid, plus formation_energy_peratom / ehull when
present (kept for the future stability-validation layer; ignored by the current model).
JARVIS marks missing values as the string "na"; those rows are dropped here.
"""
import argparse
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from ml.config import DATA_RAW

GAP_FIELDS = ("optb88vdw_bandgap", "mbj_bandgap", "hse_gap")
KEEP_FIELDS = ("jid", "formation_energy_peratom", "ehull")


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")  # "na", None, ""


def records_to_frame(records, target="optb88vdw_bandgap", dataset="dft_3d"):
    """List of JARVIS dicts -> DataFrame(formula, band_gap, source, [jid, formation_energy_peratom, ehull])."""
    if target not in GAP_FIELDS:
        raise ValueError(f"--target must be one of {GAP_FIELDS}")
    rows = []
    for rec in records:
        gap = _number(rec.get(target))
        if gap != gap or not rec.get("formula"):  # NaN or no formula
            continue
        row = {"formula": rec["formula"], "band_gap": gap, "source": f"jarvis_{dataset}"}
        for field in KEEP_FIELDS:
            if field in rec:
                row[field] = rec[field] if field == "jid" else _number(rec[field])
        rows.append(row)
    return pd.DataFrame(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", default="dft_3d", help="JARVIS dataset name (default: dft_3d)")
    parser.add_argument("--target", default="optb88vdw_bandgap", choices=GAP_FIELDS)
    parser.add_argument("--out", help="output CSV (default: ml/data/raw/jarvis_<dataset>.csv)")
    parser.add_argument("--with-structures", action="store_true", help="also write <out>.atoms.json.gz (jid -> atoms)")
    args = parser.parse_args(argv)

    from jarvis.db.figshare import data  # imported late so --help works without jarvis-tools

    print(f"downloading {args.dataset} ...", file=sys.stderr)
    records = data(args.dataset)
    df = records_to_frame(records, args.target, args.dataset)
    out = Path(args.out) if args.out else DATA_RAW / f"jarvis_{args.dataset}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"{len(records)} records -> {len(df)} rows with a {args.target} -> {out}", file=sys.stderr)

    if args.with_structures:
        keep = set(df["jid"]) if "jid" in df else None
        atoms = {r["jid"]: r["atoms"] for r in records if keep is None or r["jid"] in keep}
        with gzip.open(out.with_suffix(".atoms.json.gz"), "wt") as fh:
            json.dump(atoms, fh)
        print(f"saved {len(atoms)} structures", file=sys.stderr)


if __name__ == "__main__":
    main()
