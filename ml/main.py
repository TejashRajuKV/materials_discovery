"""ML engine CLI. Every command prints one JSON document on stdout (logs go to stderr),
so the Express backend can drive it as a subprocess.

  python ml/main.py bootstrap [--file data.csv]   # (synthetic or your data) -> preprocess -> train -> export
  python ml/main.py generate-data | preprocess | train [--tune] | export
  python ml/main.py predict --formulas NaCl MgO   (or JSON {"formulas": [...]} on stdin with --stdin)
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
    """Write materials.json (known data + model predictions) consumed by backend seeding."""
    import pandas as pd

    from ml.config import DATA_PROCESSED, MODELS_SAVED, PROCESSED_FILE, TARGET
    from ml.prediction.predict import load_bundle, predict_many
    from ml.training.train import METADATA_NAME

    df = pd.read_csv(DATA_PROCESSED / PROCESSED_FILE)
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
    metadata = json.loads((MODELS_SAVED / TARGET / METADATA_NAME).read_text())
    out = {"materials": materials, "model": metadata}
    (DATA_PROCESSED / "export.json").write_text(json.dumps(out))
    return {"materials": len(materials), "model_version": metadata["version"]}


def main(argv=None):
    from ml.config import DATA_RAW, RAW_DEFAULT_FILE

    parser = argparse.ArgumentParser(prog="ml")
    sub = parser.add_subparsers(dest="command", required=True)
    def add_dataset_args(sp):
        sp.add_argument("--file", help="dataset path, or a file name inside ml/data/raw/ (csv/tsv/json)")
        sp.add_argument("--formula-col", help="formula column name (auto-detected if omitted)")
        sp.add_argument("--target-col", help="band gap column name, in eV (auto-detected if omitted)")

    add_dataset_args(sub.add_parser("bootstrap"))
    sub.add_parser("generate-data")
    add_dataset_args(sub.add_parser("preprocess"))
    t = sub.add_parser("train")
    t.add_argument("--tune", action="store_true")
    sub.add_parser("export")
    p = sub.add_parser("predict")
    p.add_argument("--formulas", nargs="*", default=[])
    p.add_argument("--stdin", action="store_true")
    sub.add_parser("discover").add_argument("--stdin", action="store_true")
    e = sub.add_parser("explain")
    e.add_argument("--formula", required=True)
    args = parser.parse_args(argv)

    try:
        if args.command == "generate-data":
            from scripts.data.generate_synthetic_dataset import main as gen
            result = {"path": str(gen())}
        elif args.command == "preprocess":
            from ml.preprocessing.preprocessing_pipeline import run
            result = run(args.file or RAW_DEFAULT_FILE, args.formula_col, args.target_col)
        elif args.command == "train":
            from ml.experiments.experiment_runner import run_experiment
            result = run_experiment(tune=args.tune)
        elif args.command == "export":
            result = _export_materials()
        elif args.command == "bootstrap":
            from ml.experiments.experiment_runner import run_experiment
            from ml.preprocessing.preprocessing_pipeline import run
            from scripts.data.generate_synthetic_dataset import main as gen
            if not args.file and not (DATA_RAW / RAW_DEFAULT_FILE).exists():
                gen()
            run(args.file or RAW_DEFAULT_FILE, args.formula_col, args.target_col)
            run_experiment()
            result = _export_materials()
        elif args.command == "predict":
            from ml.prediction.predict import predict_many
            formulas = _read_stdin().get("formulas", []) if args.stdin else args.formulas
            result = {"predictions": predict_many(formulas)}
        elif args.command == "discover":
            from ml.discovery.candidate_search import run_discovery
            payload = _read_stdin()
            result = run_discovery(payload.get("spec", payload), generate=payload.get("generate", True),
                                   include_known=payload.get("include_known", True),
                                   top_k=int(payload.get("top_k", 25)))
        elif args.command == "explain":
            from ml.explainability.prediction_explanation import explain
            from ml.prediction.predict import load_bundle
            result = explain(args.formula, load_bundle())
    except Exception as exc:  # surface a structured error to the caller
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}))
        return 1
    print(json.dumps(result, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
