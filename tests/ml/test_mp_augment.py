import numpy as np
import pandas as pd
import pytest

from ml.preprocessing.mp_augment import mp_only_rows


def test_harmonises_scale_and_keeps_only_formulas_jarvis_lacks():
    jarvis = pd.DataFrame({"formula": ["NaCl", "MgO", "ZnS"], "band_gap": [5.0, 4.0, 3.0]})
    # PBE is 0.2 eV above JARVIS on the shared formulas (a pure shift, slope 1, intercept -0.2)
    mp = pd.DataFrame({"formula": ["NaCl", "MgO", "ZnS", "GaN", "AlN"], "pbe_gap": [5.2, 4.2, 3.2, 3.0, 0.1]})
    rows, info = mp_only_rows(jarvis, mp_df=mp)
    assert set(rows["formula"]) == {"GaN", "AlN"}  # shared formulas are not added again
    assert info["slope"] == pytest.approx(1.0) and info["intercept"] == pytest.approx(-0.2)
    assert rows.set_index("formula").loc["GaN", "label"] == pytest.approx(2.8)
    assert rows.set_index("formula").loc["AlN", "label"] == pytest.approx(0.0)  # clipped at zero
    assert np.all(rows["label"] >= 0)


def test_refuses_to_harmonise_without_shared_formulas():
    jarvis = pd.DataFrame({"formula": ["NaCl"], "band_gap": [5.0]})
    mp = pd.DataFrame({"formula": ["GaN", "AlN"], "pbe_gap": [3.0, 0.1]})
    with pytest.raises(ValueError, match="too few shared"):
        mp_only_rows(jarvis, mp_df=mp)
