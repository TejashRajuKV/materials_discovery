"""Dataset loading + cleaning: detect columns, parse formulas, drop invalid rows, de-duplicate."""
import warnings
from pathlib import Path

import pandas as pd

from ml.config import DATA_RAW, RAW_FORMULA_COL, RAW_TARGET_COL

warnings.filterwarnings("ignore", message="No Pauling electronegativity")

FORMULA_ALIASES = ["formula", "pretty_formula", "reduced_formula", "full_formula", "composition",
                   "chemical_formula", "compound", "material"]
TARGET_ALIASES = ["band_gap", "bandgap", "band gap", "gap expt", "gap_expt", "gap", "eg", "e_gap",
                  "optb88vdw_bandgap", "mbj_bandgap", "target"]


def resolve_path(file):
    """A bare name is looked up in ml/data/raw/; anything else is used as given."""
    path = Path(file)
    if not path.exists() and not path.is_absolute() and (DATA_RAW / path).exists():
        return DATA_RAW / path
    return path


def _find_column(columns, explicit, aliases, what):
    lowered = {str(c).strip().lower(): c for c in columns}
    if explicit:
        if explicit not in columns:
            raise ValueError(f"{what} column {explicit!r} not found; columns are {list(columns)}")
        return explicit
    for alias in aliases:
        if alias in lowered:
            return lowered[alias]
    raise ValueError(f"cannot detect the {what} column among {list(columns)}; pass it explicitly")


def _formula_from_structure(value):
    from pymatgen.core import Structure

    return Structure.from_dict(value).composition.reduced_formula if isinstance(value, dict) else value.composition.reduced_formula


def load_raw(file, formula_col=None, target_col=None):
    """Read csv/tsv/json (optionally .gz) and return a frame with columns formula, band_gap, source[, ...].

    If there is no formula column but a `structure` column (pymatgen dicts / Structures, as in the
    Matbench datasets), the formula is derived from it. The target is assumed to be in eV.
    """
    path = resolve_path(file)
    suffixes = [s.lower() for s in path.suffixes]
    if ".json" in suffixes:
        df = pd.read_json(path, orient="split") if _looks_like_split(path) else pd.read_json(path)
    elif ".tsv" in suffixes:
        df = pd.read_csv(path, sep="\t")
    else:
        df = pd.read_csv(path)

    if formula_col is None and "structure" in df.columns and not any(a in {str(c).lower() for c in df.columns} for a in FORMULA_ALIASES):
        df["formula"] = df["structure"].map(_formula_from_structure)
        formula_col = "formula"
    formula_col = _find_column(df.columns, formula_col, FORMULA_ALIASES, "formula")
    target_col = _find_column(df.columns, target_col, TARGET_ALIASES, "band gap")

    out = pd.DataFrame({RAW_FORMULA_COL: df[formula_col], RAW_TARGET_COL: df[target_col]})
    out["source"] = df["source"] if "source" in df.columns else path.name.split(".")[0]
    return out


def _looks_like_split(path):
    import gzip
    import json

    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt") as fh:
        head = fh.read(2000).lstrip()
    return head.startswith("{") and '"columns"' in head and '"data"' in head


def canonical_formula(formula):
    """Return the reduced formula, or None when the string is not a valid composition."""
    from ml.representation.material_representation import InvalidMaterialError, parse_formula

    try:
        return parse_formula(formula).reduced_formula
    except InvalidMaterialError:
        return None


def clean(df):
    """Clean a frame from load_raw. Returns (clean_df, report) where report counts every drop."""
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
