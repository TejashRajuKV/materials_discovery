"""ML engine CLI. Every command prints one JSON document on stdout (logs go to stderr),
so the Express backend can drive it as a subprocess.

  python ml/main.py bootstrap                 # JARVIS preprocess -> train -> export
  python ml/main.py preprocess [--dataset jarvis|synthetic]
  python ml/main.py generate-data | train [--tune] | export
  python ml/main.py train-property --property formation_energy|bulk_modulus
  python ml/main.py predict --formulas NaCl MgO [--property band_gap|formation_energy|bulk_modulus]
                                                  (or JSON {"formulas": [...], "property": ...} with --stdin)
  python ml/main.py discover --stdin              (JSON spec on stdin)
  python ml/main.py explain --formula MgO
"""
import argparse
import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
warnings.filterwarnings("ignore")


def _read_stdin():
    return json.loads(sys.stdin.read() or "{}")


def _export_materials():
    """Write export.json (known data + model predictions) consumed by backend seeding."""
    import pandas as pd

    from ml.config import DATA_PROCESSED, MODELS_SAVED, TARGET, TRAINING_FILE
    from ml.discovery.known_lookup import load_property_records
    from ml.prediction.predict import load_bundle, predict_many
    from ml.preprocessing.jarvis import PROPERTY_FIELDS
    from ml.training.property_models import PROPERTY_NAMES, predict_property_many
    from ml.training.train import METADATA_NAME

    df = pd.read_csv(DATA_PROCESSED / TRAINING_FILE)
    bundle = load_bundle()
    preds = predict_many(df["formula"].tolist(), bundle)
    materials = []
    for row, pred in zip(df.to_dict("records"), preds):
        materials.append({
            "formula": row["formula"],
            "band_gap": row[TARGET],
            "source": row.get("source", "unknown"),
            "predicted_band_gap": pred.get("prediction"),
            "uncertainty": pred.get("uncertainty"),
        })
    # Recorded and predicted values for every other property, one entry per (formula, property).
    properties = []
    formulas = df["formula"].tolist()
    for prop in PROPERTY_NAMES:
        recorded = load_property_records(prop)
        if not recorded:
            continue
        predicted = predict_property_many(prop, formulas)
        unit = PROPERTY_FIELDS[prop]["unit"]
        for formula, pred in zip(formulas, predicted):
            if formula not in recorded and "error" in pred:
                continue
            properties.append({
                "formula": formula, "property": prop, "unit": unit,
                "recorded": recorded.get(formula),
                "predicted": pred.get("prediction"), "uncertainty": pred.get("uncertainty"),
                "interval_low": pred.get("interval_low"), "interval_high": pred.get("interval_high"),
                "model_version": pred.get("model_version"),
            })
    metadata = json.loads((MODELS_SAVED / TARGET / METADATA_NAME).read_text())
    out = {"materials": materials, "properties": properties, "model": metadata}
    (DATA_PROCESSED / "export.json").write_text(json.dumps(out))
    return {"materials": len(materials), "property_rows": len(properties), "model_version": metadata["version"]}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ml")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("bootstrap")
    sub.add_parser("generate-data")
    pre = sub.add_parser("preprocess")
    pre.add_argument("--dataset", choices=["jarvis", "synthetic"], default="jarvis")
    t = sub.add_parser("train")
    t.add_argument("--tune", action="store_true")
    tp = sub.add_parser("train-property")
    tp.add_argument("--property", required=True, choices=["formation_energy", "bulk_modulus"])
    sub.add_parser("export")
    p = sub.add_parser("predict")
    p.add_argument("--formulas", nargs="*", default=[])
    p.add_argument("--property", default="band_gap", choices=["band_gap", "formation_energy", "bulk_modulus"])
    p.add_argument("--stdin", action="store_true")
    sub.add_parser("discover").add_argument("--stdin", action="store_true")
    e = sub.add_parser("explain")
    e.add_argument("--formula", required=True)
    args = parser.parse_args(argv)

    from ml import commands

    try:
        if args.command == "generate-data":
            from scripts.data.generate_synthetic_dataset import main as gen
            result = {"path": str(gen())}
        elif args.command == "preprocess":
            from ml.preprocessing.preprocessing_pipeline import run
            result = run(source=args.dataset)
        elif args.command == "train":
            from ml.experiments.experiment_runner import run_experiment
            result = run_experiment(tune=args.tune)
        elif args.command == "export":
            result = _export_materials()
        elif args.command == "bootstrap":
            from ml.experiments.experiment_runner import run_experiment
            from ml.preprocessing.preprocessing_pipeline import run
            run(source="jarvis")
            run_experiment()
            result = _export_materials()
        elif args.command == "train-property":
            from ml.training.property_models import train_property
            meta = train_property(args.property)
            result = {"property": args.property, "best_model": meta["best_model"], "version": meta["version"],
                      "test_mae": meta["results"][meta["best_model"]]["test"]["mae"]}
        elif args.command == "predict":
            payload = _read_stdin() if args.stdin else {}
            formulas = payload.get("formulas", []) if args.stdin else args.formulas
            prop = payload.get("property", args.property) if args.stdin else args.property
            result = commands.predict(formulas, prop)
        elif args.command == "discover":
            result = commands.discover(_read_stdin())
        elif args.command == "explain":
            result = commands.explain(args.formula)
    except Exception as exc:  # surface a structured error to the caller
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}))
        return 1
    print(json.dumps(result, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
