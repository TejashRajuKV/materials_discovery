import itertools
import json

import pandas as pd
import pytest

from ml.preprocessing import preprocessing_pipeline as pipeline
from ml.preprocessing.cleaning import canonical_formula
from ml.preprocessing.jarvis import load_jarvis_band_gap


def _write_source(tmp_path, formulas, optb=None, mbj=None):
    """Write a materials.csv + targets/band_gap.csv pair shaped like scripts/data/to_csv.py output."""
    materials = tmp_path / "materials.csv"
    targets = tmp_path / "band_gap.csv"
    pd.DataFrame({"jid": [f"JVASP-{i}" for i in range(len(formulas))], "formula": formulas,
                  "nat": 2, "func": "OptB88vdW"}).to_csv(materials, index=False)
    rows = []
    for i, gap in enumerate(optb or []):
        rows.append([f"JVASP-{i}", "band_gap", gap, "eV", "OptB88vdW", "JARVIS dft_3d"])
    for i, gap in enumerate(mbj or []):
        rows.append([f"JVASP-{i}", "band_gap", gap, "eV", "TBmBJ", "JARVIS dft_3d"])
    pd.DataFrame(rows, columns=["jid", "property", "value", "unit", "method", "source"]).to_csv(
        targets, index=False)
    return materials, targets


def test_loader_keeps_only_requested_method_and_joins_formula(tmp_path):
    materials, targets = _write_source(
        tmp_path, formulas=["NaCl", "MgO", "Si"], optb=[5.0, 0.0], mbj=[5.5])
    df = load_jarvis_band_gap(materials, targets, method="OptB88vdW")

    assert list(df.columns) == ["formula", "band_gap", "source", "jid"]
    assert dict(zip(df.jid, zip(df.formula, df.band_gap))) == {
        "JVASP-0": ("NaCl", 5.0),
        "JVASP-1": ("MgO", 0.0),  # zero gap (metal) is a real value, not missing
    }  # Si has no OptB88vdW value and TBmBJ rows are excluded


def test_loader_uses_tbmbj_when_asked(tmp_path):
    materials, targets = _write_source(tmp_path, formulas=["NaCl", "MgO"], optb=[5.0, 0.0], mbj=[6.1])
    df = load_jarvis_band_gap(materials, targets, method="TBmBJ")
    assert df.to_dict("records") == [
        {"formula": "NaCl", "band_gap": 6.1, "source": "JARVIS dft_3d", "jid": "JVASP-0"}]


def test_loader_reports_missing_files(tmp_path):
    with pytest.raises(FileNotFoundError, match="to_csv.py"):
        load_jarvis_band_gap(tmp_path / "nope.csv", tmp_path / "nope2.csv")


def test_loader_rejects_unknown_method(tmp_path):
    materials, targets = _write_source(tmp_path, formulas=["NaCl"], optb=[5.0])
    with pytest.raises(ValueError, match="HSE"):
        load_jarvis_band_gap(materials, targets, method="HSE")


def test_pipeline_writes_training_table_from_jarvis(tmp_path, monkeypatch):
    # 66 distinct binary compositions (all pairs of 12 common elements), plus one repeated
    # formula from a second JARVIS entry, which cleaning must merge (median of the two values).
    elements = ["Li", "Na", "Mg", "Al", "Si", "P", "S", "Cl", "K", "Ca", "Ti", "Fe"]
    formulas = [f"{a}{b}" for a, b in itertools.combinations(elements, 2)]
    formulas.append(formulas[0])
    gaps = [float(i % 7) + 0.5 for i in range(len(formulas))]
    gaps[-1] = 9.5  # median of (0.5, 9.5) is 5.0

    materials, targets = _write_source(tmp_path, formulas=formulas, optb=gaps)
    monkeypatch.setattr(pipeline, "load_jarvis_band_gap",
                        lambda: load_jarvis_band_gap(materials, targets))

    out = tmp_path / "out"
    report = pipeline.run(source="jarvis", out_dir=out, extra_tables=False)  # stability and property tables need the full dataset

    assert report["valid"] and report["source"] == "jarvis"
    assert report["merged_duplicates"] == 1
    train = pd.read_csv(out / "band_gap_training.csv")
    assert list(train.columns)[:2] == ["formula", "band_gap"]
    assert train.formula.is_unique
    key = canonical_formula("LiNa")  # pymatgen orders elements by electronegativity
    assert train.set_index("formula").loc[key, "band_gap"] == pytest.approx(5.0)
    assert json.loads((out / "preprocessing_report.json").read_text())["rows_out"] == len(train)


def test_unknown_source_is_rejected():
    with pytest.raises(ValueError, match="unknown source"):
        pipeline.run(source="nope")
