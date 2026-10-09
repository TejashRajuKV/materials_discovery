"""Convert a raw JARVIS JSON file into the small CSV set under ml/data/processed/.

Reads an already-downloaded file from ml/data/raw/ and writes:

    processed/materials.csv        identity, composition, structure pointer, bulk props
    processed/structures/<jid>.json crystal structure per material, needed to
                                   recompute features and to represent candidates
    processed/targets/band_gap.csv long format: jid, property, value, unit, method
    processed/features/             empty; CFID lands in Sprint 3
    processed/splits/               empty; split strategy is still open

Missing values are written as empty cells. The source dataset encodes them as
the string 'na', which would otherwise survive into the CSVs as literal text
and break numeric dtypes on read.
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROCESSED = Path(__file__).resolve().parents[2] / "ml" / "data" / "processed"
METADATA = Path(__file__).resolve().parents[2] / "ml" / "data" / "metadata"
MISSING = {"na", "n/a", "none", "nan", "null", "-", ""}

MATERIAL_COLUMNS = [
    "jid",
    "formula",
    "nat",
    "dimensionality",
    "spg_number",
    "spg_symbol",
    "density",
    "formation_energy_peratom",
    "ehull",
    "magmom_outcar",
    "magmom_oszicar",
    "func",
    "icsd",
]

TARGETS = [
    ("mbj_bandgap", "band_gap", "eV", "TBmBJ"),
    ("optb88vdw_bandgap", "band_gap", "eV", "OptB88vdW"),
]


def clean(value):
    """Return a writable cell value, mapping every sentinel form to empty."""
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, float) and value != value:  # NaN
        return ""
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        return "" if value.strip().lower() in MISSING else value
    return json.dumps(value)


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value == value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="raw JSON filename in ml/data/raw/, e.g. dft_3d.json")
    args = parser.parse_args()

    raw_path = Path(__file__).resolve().parents[2] / "ml" / "data" / "raw" / args.source
    if not raw_path.is_file():
        print(f"error: {raw_path} not found. Download it first.", file=sys.stderr)
        return 1

    print(f"Reading {raw_path.name} ...", flush=True)
    with raw_path.open(encoding="utf-8") as handle:
        records = json.load(handle)
    print(f"  {len(records)} records", flush=True)

    structures_dir = PROCESSED / "structures"
    for sub in ("targets", "features", "splits"):
        (PROCESSED / sub).mkdir(parents=True, exist_ok=True)
    structures_dir.mkdir(parents=True, exist_ok=True)

    kept = 0
    with (PROCESSED / "materials.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MATERIAL_COLUMNS)
        writer.writeheader()
        for record in records:
            jid = record.get("jid")
            if not jid:
                continue
            writer.writerow({col: clean(record.get(col)) for col in MATERIAL_COLUMNS})
            kept += 1

            atoms = record.get("atoms")
            if isinstance(atoms, dict):
                target = structures_dir / f"{jid}.json"
                with target.open("w", encoding="utf-8") as sfh:
                    json.dump(
                        {
                            "jid": jid,
                            "lattice_mat": atoms.get("lattice_mat"),
                            "coords": atoms.get("coords"),
                            "elements": atoms.get("elements"),
                            "cartesian": atoms.get("cartesian", False),
                        },
                        sfh,
                    )

    with (PROCESSED / "targets" / "band_gap.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["jid", "property", "value", "unit", "method", "source"])
        counts = {}
        for record in records:
            jid = record.get("jid")
            if not jid:
                continue
            for field, prop, unit, method in TARGETS:
                if is_number(record.get(field)):
                    writer.writerow([jid, prop, record[field], unit, method, "JARVIS dft_3d"])
                    counts[method] = counts.get(method, 0) + 1

    for sub in ("features", "splits"):
        (PROCESSED / sub / ".gitkeep").touch()

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": args.source,
        "records_in": len(records),
        "records_written": kept,
        "targets": counts,
        "materials_csv": "ml/data/processed/materials.csv",
        "structures_dir": "ml/data/processed/structures",
        "note": "CFID features and train/validation/test splits not yet generated.",
    }
    METADATA.mkdir(parents=True, exist_ok=True)
    with (METADATA / "processed_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print(f"  materials.csv      {kept} rows", flush=True)
    for method, count in counts.items():
        print(f"  targets/band_gap   {count} rows ({method})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())