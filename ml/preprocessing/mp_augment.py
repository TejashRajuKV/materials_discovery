"""Materials Project PBE gaps as extra training labels for formulas JARVIS does not contain.

PBE and JARVIS's OptB88vdW give systematically different gaps (JARVIS is about 0.13 eV lower on
average). A linear map fitted on the formulas both sources share puts the PBE gaps on the JARVIS scale.
Only formulas absent from JARVIS are added, so no formula gets two labels.
"""
import numpy as np
import pandas as pd

from ml.config import DATA_PROCESSED, DATA_RAW
from ml.representation.material_representation import chemical_system

MP_CACHE = DATA_PROCESSED / "mp_pbe_gaps.csv"
MP_FILE = DATA_RAW / "mp_3d.json"
SOURCE = "Materials Project PBE (harmonised to JARVIS scale)"


def load_mp_gaps():
    """formula -> median PBE gap over Materials Project entries. Cached as CSV after the first read."""
    if not MP_CACHE.exists():
        from ml.validation.external_benchmark import mp_pbe_gaps
        gaps = mp_pbe_gaps(MP_FILE)
        MP_CACHE.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"formula": list(gaps), "pbe_gap": list(gaps.values())}).to_csv(MP_CACHE, index=False)
    return pd.read_csv(MP_CACHE, keep_default_na=False)


def mp_only_rows(jarvis_df, mp_df=None):
    """Materials Project formulas absent from `jarvis_df`, with harmonised labels.

    Returns (rows, info): rows has formula, label (JARVIS scale, clipped at 0), pbe_gap, system;
    info records the fitted map and the counts.
    """
    mp = load_mp_gaps() if mp_df is None else mp_df
    shared = mp.merge(jarvis_df[["formula", "band_gap"]], on="formula")
    if len(shared) < 2:
        raise ValueError("too few shared formulas to harmonise the Materials Project scale")
    slope, intercept = np.polyfit(shared["pbe_gap"], shared["band_gap"], 1)
    rows = mp[~mp["formula"].isin(jarvis_df["formula"])].reset_index(drop=True).copy()
    rows["label"] = np.clip(slope * rows["pbe_gap"] + intercept, 0.0, None)
    rows["system"] = [chemical_system(f) for f in rows["formula"]]
    info = {
        "source": SOURCE,
        "n": int(len(rows)),
        "shared_formulas_for_harmonisation": int(len(shared)),
        "slope": round(float(slope), 4),
        "intercept": round(float(intercept), 4),
    }
    return rows, info
