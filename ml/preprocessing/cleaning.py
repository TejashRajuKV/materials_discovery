"""Dataset cleaning: parse formulas, drop invalid rows, de-duplicate."""
import warnings

import pandas as pd

from ml.config import RAW_FORMULA_COL, RAW_TARGET_COL

warnings.filterwarnings("ignore", message="No Pauling electronegativity")


def canonical_formula(formula):
    """Return the reduced formula, or None when the string is not a valid composition."""
    from ml.representation.material_representation import InvalidMaterialError, parse_formula

    try:
        return parse_formula(formula).reduced_formula
    except InvalidMaterialError:
        return None


def load_raw(path):
    df = pd.read_csv(path)
    missing = {RAW_FORMULA_COL, RAW_TARGET_COL} - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    return df


def clean(df):
    """Clean a raw dataframe. Returns (clean_df, report) where report counts every drop."""
    report = {"rows_in": int(len(df))}
    df = df.copy()

    df["formula"] = df[RAW_FORMULA_COL].map(canonical_formula)
    invalid = df["formula"].isna()
    report["dropped_invalid_formula"] = int(invalid.sum())
    df = df[~invalid]

    df[RAW_TARGET_COL] = pd.to_numeric(df[RAW_TARGET_COL], errors="coerce")
    bad_target = df[RAW_TARGET_COL].isna() | (df[RAW_TARGET_COL] < 0)
    report["dropped_missing_or_negative_target"] = int(bad_target.sum())
    df = df[~bad_target]

    # Duplicates of the same reduced formula: keep the median measurement.
    before = len(df)
    extra = [c for c in df.columns if c not in ("formula", RAW_TARGET_COL, RAW_FORMULA_COL)]
    agg = {RAW_TARGET_COL: "median"}
    agg.update({c: "first" for c in extra})
    df = df.groupby("formula", as_index=False).agg(agg)
    report["merged_duplicates"] = int(before - len(df))

    report["rows_out"] = int(len(df))
    return df.reset_index(drop=True), report
