import numpy as np
import pandas as pd

from ml.discovery.candidate_generation import generate_by_substitution
from ml.evaluation.metrics import regression_metrics
from ml.optimization.constraints import InvalidSpecError, evaluate_constraints, normalize_spec
from ml.optimization.multi_objective import rank_candidates
from ml.optimization.pareto import non_dominated_ranks
from ml.preprocessing.cleaning import clean
from ml.training.cross_validation import grouped_train_test_split
from ml.validation.chemical_validation import validate_composition
import pytest


def test_clean_drops_bad_rows_and_merges_duplicates():
    raw = pd.DataFrame({"formula": ["NaCl", "Na1Cl1", "Xx9", "MgO", "CaO"],
                        "band_gap": [5.0, 5.2, 1.0, "bad", -1.0]})
    df, report = clean(raw)
    assert list(df.formula) == ["NaCl"]
    assert df.band_gap.iloc[0] == pytest.approx(5.1)
    assert report["dropped_invalid_formula"] == 1
    assert report["dropped_missing_or_negative_target"] == 2
    assert report["merged_duplicates"] == 1


def test_grouped_split_has_no_group_leakage():
    groups = np.array(["a", "a", "b", "b", "c", "c", "d", "d", "e", "e"] * 5)
    tr, te = grouped_train_test_split(len(groups), groups, test_size=0.3)
    assert not set(groups[tr]) & set(groups[te])


def test_metrics_perfect_and_mape_skips_zero():
    m = regression_metrics([0, 1, 2], [0, 1, 2])
    assert m["mae"] == 0 and m["r2"] == 1 and m["mape_nonzero"] == 0


def test_pareto_ranks():
    # (1,1) dominates (2,2); (0,3) and (3,0) are incomparable with it
    ranks = non_dominated_ranks([[1, 1], [2, 2], [0, 3], [3, 0]])
    assert ranks == [0, 1, 0, 0]


def test_constraints_and_ranking():
    spec = normalize_spec({"band_gap": {"min": 1.0, "max": 3.0, "target": 2.0}, "exclude_elements": ["Pb"]})
    ok = {"formula": "ZnS", "prediction": 2.1, "uncertainty": 0.1}
    low = {"formula": "ZnS", "prediction": 0.5, "uncertainty": 0.1}
    pb = {"formula": "PbS", "prediction": 2.0, "uncertainty": 0.1}
    assert evaluate_constraints(ok, spec)["satisfied"]
    assert not evaluate_constraints(low, spec)["satisfied"]
    assert not evaluate_constraints(pb, spec)["satisfied"]
    a = {"formula": "A", "prediction": 2.0, "uncertainty": 0.3}
    b = {"formula": "B", "prediction": 2.4, "uncertainty": 0.1}
    c = {"formula": "C", "prediction": 2.5, "uncertainty": 0.4}  # dominated by both
    ranked = rank_candidates([a, b, c], spec)
    assert {x["formula"]: x["pareto_rank"] for x in ranked} == {"A": 0, "B": 0, "C": 1}


@pytest.mark.parametrize("spec", [{}, {"band_gap": {"min": 3, "max": 1}}, {"band_gap": {"min": "x"}}])
def test_invalid_specs_rejected(spec):
    with pytest.raises(InvalidSpecError):
        normalize_spec(spec)


def test_chemical_validation_layers():
    assert validate_composition("NaCl")["status"] == "pass"
    assert validate_composition("NaCl2")["status"] == "warn"
    assert validate_composition("Xx9")["status"] == "fail"
    assert validate_composition("HeO")["status"] == "fail"


def test_generation_excludes_known_and_is_deterministic():
    known = ["NaCl", "KBr", "MgO", "CaS"]
    out = generate_by_substitution(known, limit=50)
    assert out and not set(out) & set(known)
    assert out == generate_by_substitution(known, limit=50)
    assert "KCl" in generate_by_substitution(known, limit=500)


def test_load_raw_detects_columns_and_derives_source(tmp_path):
    from ml.preprocessing.cleaning import load_raw
    f = tmp_path / "mp_gaps.csv"
    pd.DataFrame({"pretty_formula": ["NaCl", "GaAs"], "Eg": [5.0, 0.2], "other": [1, 2]}).to_csv(f, index=False)
    df = load_raw(f)
    assert list(df.columns) == ["formula", "band_gap", "source"]
    assert df.source.unique().tolist() == ["mp_gaps"]
    assert df.band_gap.tolist() == [5.0, 0.2]


def test_load_raw_explicit_columns_and_errors(tmp_path):
    from ml.preprocessing.cleaning import load_raw
    f = tmp_path / "d.csv"
    pd.DataFrame({"name": ["NaCl"], "val": [5.0]}).to_csv(f, index=False)
    with pytest.raises(ValueError, match="cannot detect the formula"):
        load_raw(f)
    assert load_raw(f, "name", "val").band_gap.iloc[0] == 5.0
    with pytest.raises(ValueError, match="not found"):
        load_raw(f, "nope", "val")


def test_load_raw_from_structure_column_and_json(tmp_path):
    from pymatgen.core import Lattice, Structure
    from ml.preprocessing.cleaning import load_raw
    s = Structure(Lattice.cubic(5.64), ["Na", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])
    f = tmp_path / "mb.json"
    pd.DataFrame({"structure": [s.as_dict()], "gap pbe": [5.0]}).to_json(f)
    df = load_raw(f, target_col="gap pbe")
    assert df.formula.iloc[0] == "NaCl"


def test_jarvis_records_to_frame_drops_na_and_keeps_stability_columns(tmp_path):
    from scripts.data.download_jarvis import records_to_frame
    from ml.preprocessing.cleaning import load_raw
    records = [
        {"jid": "JVASP-1", "formula": "Si", "optb88vdw_bandgap": 0.73, "mbj_bandgap": "na", "ehull": 0.0, "formation_energy_peratom": 0.0},
        {"jid": "JVASP-2", "formula": "NaCl", "optb88vdw_bandgap": "5.1", "mbj_bandgap": 7.0, "ehull": "na"},
        {"jid": "JVASP-3", "formula": "Fe", "optb88vdw_bandgap": "na"},
        {"jid": "JVASP-4", "formula": "", "optb88vdw_bandgap": 1.0},
    ]
    df = records_to_frame(records)
    assert df.formula.tolist() == ["Si", "NaCl"] and df.band_gap.tolist() == [0.73, 5.1]
    assert set(df.source) == {"jarvis_dft_3d"} and "ehull" in df.columns
    assert records_to_frame(records, "mbj_bandgap").formula.tolist() == ["NaCl"]
    with pytest.raises(ValueError):
        records_to_frame(records, "nonsense")
    f = tmp_path / "j.csv"
    df.to_csv(f, index=False)
    assert load_raw(f).band_gap.tolist() == [0.73, 5.1]  # round-trips through the loader


def test_binned_intervals_cover_at_the_target_rate_and_adapt_to_regime():
    from ml.prediction.calibration import empirical_coverage, fit_binned_intervals, halfwidths, interval
    rng = np.random.default_rng(1)
    def sample(n):
        pred = rng.uniform(0, 6, n)
        noise_scale = np.where(pred < 2, 0.05, 0.5)          # heteroscedastic: easy low gaps, hard high gaps
        return pred, pred + rng.normal(0, 1, n) * noise_scale
    p_cal, y_cal = sample(4000)
    cal = fit_binned_intervals(p_cal, y_cal, alpha=0.1)
    p_te, y_te = sample(4000)
    assert 0.86 <= empirical_coverage(cal, p_te, y_te) <= 0.94
    low, high = halfwidths(cal, [0.5]), halfwidths(cal, [5.0])
    assert high[0] > 3 * low[0]                                # wider where the model is less accurate
    lo, hi = interval(cal, [0.01])
    assert lo[0] == 0 and hi[0] > 0.01                         # never below zero
