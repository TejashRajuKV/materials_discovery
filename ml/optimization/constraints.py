"""User-defined requirements for a discovery job.

spec = {
  "band_gap": {"min": 1.0, "max": 3.0, "target": 2.0},   # eV; all keys optional
  "max_uncertainty": 0.5,
  "include_elements": ["O"], "exclude_elements": ["Pb"],
  "max_elements": 3,
}
"""
from ml.config import TARGET
from ml.representation.material_representation import parse_formula


class InvalidSpecError(ValueError):
    pass


def normalize_spec(spec):
    spec = dict(spec or {})
    band = dict(spec.get(TARGET) or {})
    for key in ("min", "max", "target"):
        if band.get(key) in ("", None):
            band.pop(key, None)
        else:
            try:
                band[key] = float(band[key])
            except (TypeError, ValueError) as exc:
                raise InvalidSpecError(f"{TARGET}.{key} must be a number") from exc
    if "min" in band and "max" in band and band["min"] > band["max"]:
        raise InvalidSpecError(f"{TARGET}.min must not exceed {TARGET}.max")
    if not band and not any(k in spec for k in ("include_elements", "exclude_elements", "max_elements")):
        raise InvalidSpecError("specify at least one requirement (property range/target or element constraint)")
    spec[TARGET] = band
    spec["include_elements"] = [str(e) for e in spec.get("include_elements") or []]
    spec["exclude_elements"] = [str(e) for e in spec.get("exclude_elements") or []]
    spec["max_uncertainty"] = float(spec["max_uncertainty"]) if spec.get("max_uncertainty") not in (None, "") else None
    spec["max_elements"] = int(spec["max_elements"]) if spec.get("max_elements") not in (None, "") else None
    return spec


def evaluate_constraints(candidate, spec):
    """candidate needs: formula, prediction, uncertainty. Returns {satisfied, checks}."""
    checks = []
    value = candidate["prediction"]
    band = spec[TARGET]
    if "min" in band:
        checks.append({"name": f"{TARGET} >= {band['min']}", "ok": value >= band["min"], "detail": f"{value:.3f}"})
    if "max" in band:
        checks.append({"name": f"{TARGET} <= {band['max']}", "ok": value <= band["max"], "detail": f"{value:.3f}"})

    symbols = {e.symbol for e in parse_formula(candidate["formula"]).elements}
    if spec["include_elements"]:
        missing = [e for e in spec["include_elements"] if e not in symbols]
        checks.append({"name": "includes required elements", "ok": not missing, "detail": ", ".join(missing) or "ok"})
    if spec["exclude_elements"]:
        present = sorted(symbols & set(spec["exclude_elements"]))
        checks.append({"name": "avoids excluded elements", "ok": not present, "detail": ", ".join(present) or "ok"})
    if spec["max_elements"] is not None:
        checks.append({"name": f"<= {spec['max_elements']} elements", "ok": len(symbols) <= spec["max_elements"],
                       "detail": str(len(symbols))})
    if spec["max_uncertainty"] is not None:
        checks.append({"name": f"uncertainty <= {spec['max_uncertainty']}", "ok": candidate["uncertainty"] <= spec["max_uncertainty"],
                       "detail": f"{candidate['uncertainty']:.3f}"})
    return {"satisfied": all(c["ok"] for c in checks), "checks": checks}
