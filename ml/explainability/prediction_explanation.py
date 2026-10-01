"""Model-level explanations for a single prediction.

These describe what the *model* keys on and which known materials look similar in
feature space. They are NOT causal / physical explanations.
"""
import numpy as np

from ml.representation.material_representation import featurize


def explain(formula, bundle, top=5, neighbors=3):
    x = featurize(formula)
    z = (x - bundle["feature_means"]) / bundle["feature_stds"]
    impact = np.abs(z) * bundle["importances"]
    order = np.argsort(-impact)[:top]
    features = [
        {
            "feature": bundle["feature_names"][i],
            "value": round(float(x[i]), 4),
            "z_score": round(float(z[i]), 2),
            "importance": round(float(bundle["importances"][i]), 4),
        }
        for i in order
    ]

    dist, idx = bundle["neighbors"].kneighbors(bundle["scaler"].transform(x.reshape(1, -1)), n_neighbors=neighbors)
    similar = [
        {
            "formula": bundle["train_formulas"][j],
            "band_gap": round(float(bundle["train_targets"][j]), 3),
            "distance": round(float(d), 3),
        }
        for d, j in zip(dist[0], idx[0])
    ]
    return {
        "formula": formula,
        "top_features": features,
        "similar_known_materials": similar,
        "mean_neighbor_distance": round(float(dist[0].mean()), 3),
        "disclaimer": "Model-level explanation (feature influence + nearest known materials); not a causal claim.",
    }
