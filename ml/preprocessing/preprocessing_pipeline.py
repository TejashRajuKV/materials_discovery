"""Raw dataset file -> cleaned, validated CSV plus a JSON report."""
import json

from ml.config import DATA_PROCESSED, PROCESSED_FILE, RAW_DEFAULT_FILE
from ml.preprocessing.cleaning import clean, load_raw, resolve_path
from ml.preprocessing.validation import describe_target, validate_dataset


def run(raw_file=RAW_DEFAULT_FILE, formula_col=None, target_col=None):
    path = resolve_path(raw_file)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Pass --file with a CSV/JSON containing a formula and a band gap column "
            "(in eV), or run `python ml/main.py generate-data` for the synthetic demo set."
        )
    df, report = clean(load_raw(path, formula_col, target_col))
    ok, problems = validate_dataset(df)
    report.update({"raw_file": path.name, "valid": ok, "problems": problems, "target": describe_target(df),
                   "sources": sorted(df["source"].astype(str).unique().tolist())})
    if not ok:
        raise ValueError(f"dataset failed validation: {problems}")

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PROCESSED / PROCESSED_FILE, index=False)
    (DATA_PROCESSED / "preprocessing_report.json").write_text(json.dumps(report, indent=2))
    return report
