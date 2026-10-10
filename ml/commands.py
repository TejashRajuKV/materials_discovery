"""The ML operations that both the CLI (ml/main.py) and the resident service (ml/service.py) expose.

Each function takes plain values and returns a JSON-serialisable result. Imports are local so that a
command loads only the models it needs.
"""


def predict(formulas, prop="band_gap"):
    if prop == "band_gap":
        from ml.prediction.predict import predict_many
        return {"predictions": predict_many(formulas)}
    from ml.training.property_models import predict_property_many
    return {"predictions": predict_property_many(prop, formulas)}


def discover(payload):
    from ml.discovery.candidate_search import run_discovery
    return run_discovery(payload.get("spec", payload), generate=payload.get("generate", True),
                         include_known=payload.get("include_known", True),
                         top_k=int(payload.get("top_k", 25)))


def explain(formula):
    from ml.explainability.prediction_explanation import explain as explain_formula
    from ml.prediction.predict import load_bundle
    return explain_formula(formula, load_bundle())
