import pytest

from ml.validation.label_quality import implausible_label, is_all_metal


@pytest.mark.parametrize("formula,expected", [("AcLaNd", True), ("Fe", True), ("NaCl", False), ("MgO", False),
                                              ("GaAs", False), ("Si", False), ("Cu3Au", True), ("LiH", False)])
def test_all_metal_classification(formula, expected):
    assert is_all_metal(formula) is expected


def test_only_large_gaps_in_all_metal_compounds_are_implausible():
    assert implausible_label("AcLaNd", 11.9) is True       # intermetallic with a wide gap: artefact
    assert implausible_label("AcLaNd", 0.0) is False       # a metal with no gap is normal
    assert implausible_label("NaCl", 8.0) is False         # an ionic insulator can have a wide gap
    assert implausible_label("Fe", 1.5) is False           # below the threshold
