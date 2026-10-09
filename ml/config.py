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

# JARVIS source (written by scripts/data/to_csv.py from ml/data/raw/dft_3d.json).
# materials.csv: one row per jid (identity + composition). targets/band_gap.csv: long format,
# one row per (jid, method). The band gap is taken from one DFT method so every row has the same
# meaning; OptB88vdW covers all materials, TBmBJ only ~23% of them.
JARVIS_MATERIALS_FILE = DATA_PROCESSED / "materials.csv"
JARVIS_TARGETS_FILE = DATA_PROCESSED / "targets" / "band_gap.csv"
JARVIS_BANDGAP_METHOD = "OptB88vdW"
JARVIS_RAW_FILE = DATA_RAW / "dft_3d.json"  # full records, needed for fields not in materials.csv

# Training table written by `preprocess` and read by train / discover / export.
TRAINING_FILE = "band_gap_training.csv"
# Lowest energy-above-hull (eV/atom) per formula, from the JARVIS `ehull` field. Read by discovery.
STABILITY_FILE = "stability.csv"

# Synthetic demo set (opt-in via `preprocess --dataset synthetic`). Raw dataset contract: a CSV
# with at least these columns.
RAW_FORMULA_COL = "formula"
RAW_TARGET_COL = TARGET
RAW_DEFAULT_FILE = "synthetic_demo.csv"
