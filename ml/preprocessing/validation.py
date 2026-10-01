"""Dataset-level sanity checks run after cleaning."""
from ml.config import RAW_TARGET_COL

# Band gaps above this are almost certainly unit/parsing errors in a materials DB.
MAX_PLAUSIBLE_BAND_GAP_EV = 15.0
MIN_ROWS_FOR_TRAINING = 50


def validate_dataset(df):
    """Return (ok, problems). Hard problems make ok False."""
    problems = []
    if len(df) < MIN_ROWS_FOR_TRAINING:
        problems.append(f"only {len(df)} rows; need at least {MIN_ROWS_FOR_TRAINING}")
    if df["formula"].duplicated().any():
        problems.append("duplicate formulas remain after cleaning")
    too_big = int((df[RAW_TARGET_COL] > MAX_PLAUSIBLE_BAND_GAP_EV).sum())
    if too_big:
        problems.append(f"{too_big} rows exceed {MAX_PLAUSIBLE_BAND_GAP_EV} eV")
    return (not problems), problems


def describe_target(df):
    s = df[RAW_TARGET_COL]
    return {
        "count": int(s.count()),
        "mean": float(s.mean()),
        "std": float(s.std()),
        "min": float(s.min()),
        "max": float(s.max()),
        "fraction_zero_gap": float((s == 0).mean()),
    }
