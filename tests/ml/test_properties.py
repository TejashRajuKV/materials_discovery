import json

import pandas as pd
import pytest

from ml.optimization.constraints import InvalidSpecError, evaluate_constraints, normalize_spec
from ml.preprocessing.jarvis import build_property_table


def _fixture(tmp_path):
    raw = tmp_path / "dft_3d.json"
    raw.write_text(json.dumps([
        {"jid": "JVASP-1", "formula": "NaCl", "bulk_modulus_kv": 20.0, "formation_energy_peratom": -2.0},
        {"jid": "JVASP-2", "formula": "NaCl", "bulk_modulus_kv": 30.0, "formation_energy_peratom": -1.0},
        {"jid": "JVASP-3", "formula": "MgO", "bulk_modulus_kv": -5.0, "formation_energy_peratom": -3.0},
        {"jid": "JVASP-4", "formula": "CaO", "bulk_modulus_kv": "na", "formation_energy_peratom": -2.5},
    ]), encoding="utf-8")
    materials = tmp_path / "materials.csv"
    pd.DataFrame({
        "jid": ["JVASP-1", "JVASP-2", "JVASP-3", "JVASP-4"],
        "formula": ["NaCl", "Na1Cl1", "MgO", "CaO"],
        "ehull": [0.5, 0.01, 0.0, 0.0],
    }).to_csv(materials, index=False)
    return raw, materials


def test_property_table_uses_most_stable_entry_with_a_value(tmp_path):
    raw, materials = _fixture(tmp_path)
    table = build_property_table("formation_energy", raw_path=raw, materials_path=materials).set_index("formula")
    assert table.loc["NaCl", "value"] == pytest.approx(-1.0)  # JVASP-2 has the lower ehull
    assert table.loc["NaCl", "n_entries"] == 2
    assert table.loc["CaO", "value"] == pytest.approx(-2.5)


def test_bulk_modulus_drops_unphysical_and_missing_values(tmp_path):
    raw, materials = _fixture(tmp_path)
    table = build_property_table("bulk_modulus", raw_path=raw, materials_path=materials).set_index("formula")
    assert "MgO" not in table.index  # negative modulus is a fit artefact
    assert "CaO" not in table.index  # no value recorded
    assert table.loc["NaCl", "value"] == pytest.approx(30.0)


def test_unknown_property_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="unknown property"):
        build_property_table("band_gap", raw_path=tmp_path / "x.json", materials_path=tmp_path / "y.csv")


def test_property_ranges_are_normalised_and_checked():
    spec = normalize_spec({"formation_energy": {"max": -0.5}, "bulk_modulus": {"min": "100"}})
    assert spec["formation_energy"] == {"max": -0.5}
    assert spec["bulk_modulus"] == {"min": 100.0}
    stable = {"formula": "NaCl", "prediction": 2.0, "uncertainty": 0.1,
              "properties": {"formation_energy": {"value": -1.2}, "bulk_modulus": {"value": 150.0}}}
    assert evaluate_constraints(stable, spec)["satisfied"] is True
    assert evaluate_constraints({**stable, "properties": {"formation_energy": {"value": 0.3}}}, spec)["satisfied"] is False


def test_generated_candidates_without_a_prediction_fail_a_property_range():
    spec = normalize_spec({"bulk_modulus": {"min": 50}})
    result = evaluate_constraints({"formula": "NaCs", "prediction": 2.0, "uncertainty": 0.1}, spec)
    assert result["satisfied"] is False
    assert result["checks"][0]["detail"] == "no data"


def test_property_range_rejects_inverted_or_non_numeric_bounds():
    with pytest.raises(InvalidSpecError):
        normalize_spec({"formation_energy": {"min": 1, "max": 0}})
    with pytest.raises(InvalidSpecError):
        normalize_spec({"bulk_modulus": {"min": "stiff"}})
