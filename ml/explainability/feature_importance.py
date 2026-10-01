"""Global feature importance from the random forest (impurity-based)."""


def global_importance(bundle, top=10):
    pairs = sorted(zip(bundle["feature_names"], bundle["importances"]), key=lambda kv: -kv[1])
    return [{"feature": name, "importance": round(float(imp), 4)} for name, imp in pairs[:top]]
