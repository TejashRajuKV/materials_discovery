import json

import pytest

from ml.validation.oqmd_benchmark import oqmd_gaps


def _record(elements, gap):
    return {"_oqmd_band_gap": gap, "atoms": {"elements": elements}}


def test_formulas_are_derived_from_elements_with_trailing_spaces(tmp_path):
    path = tmp_path / "oqmd.json"
    path.write_text(json.dumps([
        _record(["Na ", "Cl "], 5.0),
        _record(["Na ", "Cl ", "Na ", "Cl "], 5.4),      # a larger cell of the same compound
        _record(["Mg ", "Mg ", "O ", "O "], 4.0),
        _record(["Fe "], 0.0),
    ]), encoding="utf-8")
    gaps, read, skipped = oqmd_gaps(path)
    assert (read, skipped) == (4, 0)
    assert gaps["NaCl"] == pytest.approx(5.2)  # median of the two entries
    assert gaps["MgO"] == 4.0 and gaps["Fe"] == 0.0


def test_unreadable_records_are_counted_and_do_not_pass_silently(tmp_path):
    path = tmp_path / "oqmd.json"
    good = _record(["Na ", "Cl "], 5.0)
    bad = [_record(["Xx9"], 1.0), {"atoms": {"elements": ["Na "]}}, _record(["Na "], -1.0)]
    path.write_text(json.dumps([good] + bad), encoding="utf-8")
    with pytest.raises(ValueError, match="could not be read"):
        oqmd_gaps(path)


def test_cached_gap_tables_keep_formulas_pandas_would_read_as_missing(tmp_path, monkeypatch):
    # "NaN" is sodium nitride (Na + N). pandas reads the string "NaN" as a missing value unless told not to.
    from ml.preprocessing import mp_augment
    from ml.validation import oqmd_benchmark

    oqmd_cache = tmp_path / "oqmd_gaps.csv"
    oqmd_cache.write_text("formula,oqmd_gap\nNaN,1.5\nNaCl,5.0\n", encoding="utf-8")
    monkeypatch.setattr(oqmd_benchmark, "OQMD_CACHE", oqmd_cache)
    assert oqmd_benchmark.load_oqmd_gaps() == {"NaN": 1.5, "NaCl": 5.0}

    mp_cache = tmp_path / "mp_pbe_gaps.csv"
    mp_cache.write_text("formula,pbe_gap\nNaN,1.7\nMgO,4.5\n", encoding="utf-8")
    monkeypatch.setattr(mp_augment, "MP_CACHE", mp_cache)
    assert set(mp_augment.load_mp_gaps()["formula"]) == {"NaN", "MgO"}
