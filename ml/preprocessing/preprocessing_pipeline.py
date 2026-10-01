"""Raw CSV -> cleaned, validated CSV plus a JSON report."""
import json

from ml.config import DATA_PROCESSED, DATA_RAW, PROCESSED_FILE, RAW_DEFAULT_FILE
from ml.preprocessing.cleaning import clean, load_raw
from ml.preprocessing.validation import describe_target, validate_dataset


def run(raw_file=RAW_DEFAULT_FILE):
    raw_path = DATA_RAW / raw_file
    if not raw_path.exists():
        raise FileNotFoundError(
            f"{raw_path} not found. Put a CSV with columns formula,band_gap there, "
            "or run `python ml/main.py generate-data` for the synthetic demo set."
        )
    df, report = clean(load_raw(raw_path))
    ok, problems = validate_dataset(df)
    report.update({"raw_file": raw_file, "valid": ok, "problems": problems, "target": describe_target(df)})
    if not ok:
        raise ValueError(f"dataset failed validation: {problems}")

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PROCESSED / PROCESSED_FILE, index=False)
    (DATA_PROCESSED / "preprocessing_report.json").write_text(json.dumps(report, indent=2))
    return report
