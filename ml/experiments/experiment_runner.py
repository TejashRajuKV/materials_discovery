"""Run a named, reproducible training experiment and record its result."""
import json
from datetime import datetime, timezone

from ml.config import EXPERIMENTS_DIR
from ml.training.train import train


def run_experiment(folder="001_baseline", tune=False, notes=""):
    metadata = train(tune=tune)
    record = {
        "experiment": folder,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "tune": tune,
        "notes": notes,
        "best_model": metadata["best_model"],
        "model_version": metadata["version"],
        "dataset_sha256_16": metadata["dataset_sha256_16"],
        "data_source": metadata["data_source"],
        "results": metadata["results"],
    }
    out = EXPERIMENTS_DIR / folder
    out.mkdir(parents=True, exist_ok=True)
    (out / f"run_{metadata['version']}.json").write_text(json.dumps(record, indent=2))
    return record
