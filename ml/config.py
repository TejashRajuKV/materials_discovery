"""Shared paths and constants for the ML engine."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ML_DIR = ROOT / "ml"

DATA_RAW = ML_DIR / "data" / "raw"
DATA_PROCESSED = ML_DIR / "data" / "processed"
MODELS_SAVED = ML_DIR / "models" / "saved"
EXPERIMENTS_DIR = ROOT / "experiments"

# Initial discovery problem: electronic property (band gap, eV) from composition.
TARGET = "band_gap"
TARGET_UNIT = "eV"
RANDOM_SEED = 42
TEST_SIZE = 0.2
CV_FOLDS = 5

# Raw dataset contract: a CSV with at least these columns.
RAW_FORMULA_COL = "formula"
RAW_TARGET_COL = TARGET
RAW_DEFAULT_FILE = "synthetic_demo.csv"
PROCESSED_FILE = "materials.csv"
