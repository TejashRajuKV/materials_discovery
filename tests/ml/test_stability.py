import pandas as pd
import pytest

from ml.optimization.constraints import InvalidSpecError, evaluate_constraints, normalize_spec
from ml.preprocessing.jarvis import build_stability_table
from ml.discovery.known_lookup import load_known_lookup
from ml.representation.crystal_system import crystal_system
from ml.validation.stability_validation import validate_stability


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
        "dimensionality": ["3D-bulk", "2D-bulk", "3D-bulk", "3D-bulk"],
        "spg_number": [225, 139, 225, 225],
        "spg_symbol": ["Fm-3m", "I4/mmm", "Fm-3m", "Fm-3m"],
    }).to_csv(materials, index=False)
    table = build_stability_table(materials).set_index("formula")
    assert table.loc["NaCl", "ehull"] == pytest.approx(0.02)  # most stable of the two polymorphs
    assert table.loc["NaCl", "n_entries"] == 2
    assert table.loc["NaCl", "dimensionality"] == "2D-bulk"  # attributes follow the most stable entry
    assert table.loc["NaCl", "spg_number"] == 139
    assert "MgO" not in table.index
    assert table.loc["CaO", "ehull"] == pytest.approx(1.5)


def test_lookup_is_empty_when_table_missing(tmp_path):
    assert load_known_lookup(tmp_path / "absent.csv") == {}


def test_lookup_reads_attributes_of_most_stable_polymorph(tmp_path):
    path = tmp_path / "stability.csv"
    rows = [
        "formula,ehull,dimensionality,spg_number,spg_symbol,n_entries",
        "NaCl,0.0,3D-bulk,225,Fm-3m,2",
        "GaN,0.1,3D-bulk,186,P6_3mc,1",
        "MoS2,0.0,2D-bulk,194,P6_3/mmc,1",
    ]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    lookup = load_known_lookup(path)
    assert lookup["NaCl"] == {"ehull": 0.0, "dimensionality": "3D-bulk", "crystal_system": "cubic"}
    assert lookup["GaN"]["crystal_system"] == "hexagonal"
    assert lookup["MoS2"]["dimensionality"] == "2D-bulk"


@pytest.mark.parametrize("spg,system", [(1, "triclinic"), (14, "monoclinic"), (62, "orthorhombic"),
                                        (136, "tetragonal"), (166, "trigonal"), (194, "hexagonal"),
                                        (225, "cubic"), (230, "cubic"), (0, None), ("x", None)])
def test_crystal_system_from_space_group(spg, system):
    assert crystal_system(spg) == system


def test_structure_constraints_apply_to_known_only():
    spec = normalize_spec({"dimensionality": ["3D-bulk"], "crystal_system": ["cubic"]})
    known = {"formula": "NaCl", "prediction": 2.0, "uncertainty": 0.1,
             "dimensionality": "3D-bulk", "crystal_system": "cubic"}
    generated = {"formula": "NaCs", "prediction": 2.0, "uncertainty": 0.1}
    assert evaluate_constraints(known, spec)["satisfied"] is True
    assert evaluate_constraints({**known, "crystal_system": "hexagonal"}, spec)["satisfied"] is False
    assert evaluate_constraints(generated, spec)["satisfied"] is False  # no structure data


def test_unknown_structure_labels_are_rejected():
    with pytest.raises(InvalidSpecError):
        normalize_spec({"crystal_system": ["square"]})
    with pytest.raises(InvalidSpecError):
        normalize_spec({"dimensionality": ["4D"]})
