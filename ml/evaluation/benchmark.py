"""Flatten training results into a comparison table (baselines vs. the mean predictor)."""


def benchmark_table(metadata):
    rows = []
    for name, res in metadata["results"].items():
        rows.append({"model": name, "cv_mae": res["cv"]["mae"], "cv_r2": res["cv"]["r2"],
                     "test_mae": res["test"]["mae"], "test_rmse": res["test"]["rmse"], "test_r2": res["test"]["r2"]})
    return sorted(rows, key=lambda r: r["test_mae"])
