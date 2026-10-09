import pandas as pd
import pytest

from ml.optimization.constraints import InvalidSpecError, evaluate_constraints, normalize_spec
from ml.preprocessing.jarvis import build_stability_table
from ml.validation.stability_validation import load_ehull_lookup, validate_stability


def _pred(formula, ehull=None, prediction=2.0, uncertainty=0.1):
    p = {"formula": formula, "prediction": prediction, "uncertainty": uncertainty}
    if ehull is not None:
        p["ehull"] = ehull
    return p


def test_layer_is_not_assessed_without_data():
    layer = validate_stability(_pred("NaCl"))
    assert layer["status"] == "not_assessed"


@pytest.mark.parametrize("ehull,status", [(0.0, "pass"), (0.02, "pass"), (0.05, "warn"), (3.0, "warn")])
def test_layer_never_hard_fails(ehull, status):
    # Most JARVIS entries sit above the hull; the layer informs, and max_ehull is the hard limit.
    assert validate_stability(_pred("NaCl", ehull=ehull))["status"] == status


def test_max_ehull_fails_unknown_stability_and_respects_limit():
    spec = normalize_spec({"band_gap": {"min": 1, "max": 3}, "max_ehull": 0.1})
    assert evaluate_constraints(_pred("NaCl", ehull=0.05), spec)["satisfied"] is True
    assert evaluate_constraints(_pred("NaCl", ehull=0.5), spec)["satisfied"] is False
    assert evaluate_constraints(_pred("NaCl"), spec)["satisfied"] is False  # unknown is not a pass


def test_spec_accepts_stability_only_and_rejects_negative():
    spec = normalize_spec({"max_ehull": "0.05"})
    assert spec["max_ehull"] == 0.05
    with pytest.raises(InvalidSpecError):
        normalize_spec({"max_ehull": -1})


def test_stability_table_keeps_lowest_ehull_per_formula(tmp_path):
    materials = tmp_path / "materials.csv"
    pd.DataFrame({
        "jid": ["JVASP-1", "JVASP-2", "JVASP-3", "JVASP-4"],
        "formula": ["NaCl", "Na1Cl1", "MgO", "CaO"],
        "ehull": [0.4, 0.02, "", "1.5"],  # JVASP-3 has no value and must be skipped
    }).to_csv(materials, index=False)
    table = build_stability_table(materials).set_index("formula")
    assert table.loc["NaCl", "ehull"] == pytest.approx(0.02)  # most stable of the two polymorphs
    assert table.loc["NaCl", "n_entries"] == 2
    assert "MgO" not in table.index
    assert table.loc["CaO", "ehull"] == pytest.approx(1.5)


def test_lookup_is_empty_when_table_missing(tmp_path):
    assert load_ehull_lookup(tmp_path / "absent.csv") == {}
