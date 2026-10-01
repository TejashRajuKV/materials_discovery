import pytest

from ml.config import MODELS_SAVED, TARGET
from ml.training.train import BUNDLE_NAME

pytestmark = pytest.mark.skipif(not (MODELS_SAVED / TARGET / BUNDLE_NAME).exists(),
                                reason="no trained model; run `python ml/main.py bootstrap`")


def test_predict_schema_and_error_handling():
    from ml.prediction.predict import predict_many
    good, bad = predict_many(["MgO", "Xx9"])
    assert {"formula", "property", "unit", "prediction", "uncertainty", "confidence"} <= set(good)
    assert good["prediction"] >= 0 and good["uncertainty"] >= 0
    assert "error" in bad


def test_discovery_respects_constraints():
    from ml.discovery.candidate_search import run_discovery
    spec = {"band_gap": {"min": 2.0, "max": 3.0}, "exclude_elements": ["O"]}
    out = run_discovery(spec, max_generated=300, top_k=10)
    for c in out["known_matches"] + out["novel_candidates"]:
        assert 2.0 <= c["prediction"] <= 3.0
        assert "O" not in c["formula"].replace("Os", "")
        assert c["validation"]["overall"] != "fail"
    ranks = [c["rank"] for c in out["novel_candidates"]]
    assert ranks == sorted(ranks)
