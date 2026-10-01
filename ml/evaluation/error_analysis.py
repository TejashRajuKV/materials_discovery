"""Where does the model fail? Error broken down by target range and material class."""
import numpy as np
import pandas as pd

from ml.evaluation.metrics import regression_metrics

ANIONS = {"O": "oxide", "S": "sulfide", "Se": "selenide", "Te": "telluride", "F": "fluoride",
          "Cl": "chloride", "Br": "bromide", "I": "iodide", "N": "nitride", "P": "phosphide", "As": "arsenide"}


def material_class(formula):
    from pymatgen.core import Composition

    symbols = {e.symbol for e in Composition(formula).elements}
    for anion, name in ANIONS.items():
        if anion in symbols:
            return name
    return "other"


def error_analysis(formulas, y_true, y_pred):
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    df = pd.DataFrame({"formula": list(formulas), "y": y_true, "pred": y_pred})
    df["abs_err"] = (df.pred - df.y).abs()
    df["class"] = df.formula.map(material_class)

    bins = [-0.001, 0.0, 1.0, 2.0, 4.0, np.inf]
    labels = ["metal(0)", "0-1", "1-2", "2-4", ">4"]
    df["gap_bin"] = pd.cut(df.y, bins=bins, labels=labels)

    def group_table(col):
        out = {}
        for key, g in df.groupby(col, observed=True):
            if len(g) >= 3:
                out[str(key)] = regression_metrics(g.y, g.pred)
        return out

    q = df.abs_err.quantile([0.5, 0.9, 0.99])
    return {
        "error_quantiles": {"p50": float(q[0.5]), "p90": float(q[0.9]), "p99": float(q[0.99])},
        "by_gap_range": group_table("gap_bin"),
        "by_material_class": group_table("class"),
        "worst_cases": df.nlargest(10, "abs_err")[["formula", "y", "pred", "abs_err"]].round(3).to_dict("records"),
    }
