"""Source table -> cleaned, validated training table plus a JSON report.

Sources:
  jarvis     (default) JARVIS dft_3d band gaps from ml/data/processed/ (see scripts/data/to_csv.py)
  synthetic  the placeholder CSV from `generate-data`, ml/data/raw/synthetic_demo.csv
"""
import json

from ml.config import DATA_PROCESSED, DATA_RAW, RAW_DEFAULT_FILE, STABILITY_FILE, TRAINING_FILE
from ml.preprocessing.cleaning import clean, load_raw
from ml.preprocessing.jarvis import PROPERTY_FIELDS, build_property_table, build_stability_table, load_jarvis_band_gap
from ml.preprocessing.validation import describe_target, validate_dataset

SOURCES = ("jarvis", "synthetic")


def load_source(source):
    if source == "jarvis":
        return load_jarvis_band_gap()
    if source == "synthetic":
        raw_path = DATA_RAW / RAW_DEFAULT_FILE
        if not raw_path.exists():
            raise FileNotFoundError(
                f"{raw_path} not found. Run `python ml/main.py generate-data` for the synthetic demo set."
            )
        return load_raw(raw_path)
    raise ValueError(f"unknown source {source!r}; expected one of {SOURCES}")


def run(source="jarvis", out_dir=DATA_PROCESSED, extra_tables=True):
    """Write the training table; for JARVIS also the stability and property tables, unless extra_tables is False."""
    raw = load_source(source)
    df, report = clean(raw)
    ok, problems = validate_dataset(df)
    report.update({"source": source, "valid": ok, "problems": problems, "target": describe_target(df)})
    if not ok:
        raise ValueError(f"dataset failed validation: {problems}")

    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / TRAINING_FILE, index=False)
    if source == "jarvis" and extra_tables:
        stability = build_stability_table()
        stability.to_csv(out_dir / STABILITY_FILE, index=False)
        report["stability"] = {"formulas": int(len(stability)), "below_0.025_eV_per_atom": int((stability.ehull <= 0.025).sum())}
        props_dir = out_dir / "properties"
        props_dir.mkdir(parents=True, exist_ok=True)
        for prop in PROPERTY_FIELDS:
            table = build_property_table(prop)
            table.to_csv(props_dir / f"{prop}.csv", index=False)
            report[f"property_{prop}"] = int(len(table))
    (out_dir / "preprocessing_report.json").write_text(json.dumps(report, indent=2))
    return report
