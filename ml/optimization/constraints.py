"""User-defined requirements for a discovery job.

spec = {
  "band_gap": {"min": 1.0, "max": 3.0, "target": 2.0},   # eV; all keys optional
  "max_uncertainty": 0.5,
  "include_elements": ["O"], "exclude_elements": ["Pb"],
  "max_elements": 3,
  "max_ehull": 0.05,   # eV/atom above the convex hull; unknown for generated candidates (fails)
  "formation_energy": {"max": 0.0},       # eV/atom; known = recorded, generated = predicted
  "bulk_modulus": {"min": 100},           # GPa
  "dimensionality": ["3D-bulk"],          # known materials only; generated candidates fail
  "crystal_system": ["cubic", "hexagonal"],  # known materials only; generated candidates fail
}
"""
from ml.config import TARGET
from ml.representation.crystal_system import CRYSTAL_SYSTEMS
from ml.representation.material_representation import parse_formula

# Other properties with min/max ranges. Known materials use the recorded value; generated candidates use
# the model's prediction, so the check applies to them too. Units: formation energy eV/atom, bulk modulus GPa.
RANGE_PROPERTIES = ("formation_energy", "bulk_modulus")

# JARVIS dimensionality labels, as stored in the stability table.
DIMENSIONALITY_LABELS = ("3D-bulk", "2D-bulk", "1D-bulk", "0D-bulk", "intercalated ion", "intercalated molecule")


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
    if not band and not any(k in spec for k in STRUCTURE_KEYS):
        raise InvalidSpecError("specify at least one requirement (property range/target or element constraint)")
    spec[TARGET] = band
    spec["include_elements"] = [str(e) for e in spec.get("include_elements") or []]
    spec["exclude_elements"] = [str(e) for e in spec.get("exclude_elements") or []]
    spec["max_uncertainty"] = float(spec["max_uncertainty"]) if spec.get("max_uncertainty") not in (None, "") else None
    spec["max_elements"] = int(spec["max_elements"]) if spec.get("max_elements") not in (None, "") else None
    spec["max_ehull"] = _nonneg_float(spec, "max_ehull")
    for prop in RANGE_PROPERTIES:
        spec[prop] = _range(spec, prop)
    spec["dimensionality"] = _choices(spec, "dimensionality", DIMENSIONALITY_LABELS)
    spec["crystal_system"] = _choices(spec, "crystal_system", CRYSTAL_SYSTEMS)
    return spec


STRUCTURE_KEYS = ("include_elements", "exclude_elements", "max_elements", "max_ehull", "dimensionality", "crystal_system",
                  *RANGE_PROPERTIES)


def _range(spec, prop):
    """Optional {min, max} for a property; None when neither bound is given."""
    raw = spec.get(prop) or {}
    bounds = {}
    for key in ("min", "max"):
        if raw.get(key) not in (None, ""):
            try:
                bounds[key] = float(raw[key])
            except (TypeError, ValueError) as exc:
                raise InvalidSpecError(f"{prop}.{key} must be a number") from exc
    if "min" in bounds and "max" in bounds and bounds["min"] > bounds["max"]:
        raise InvalidSpecError(f"{prop}.min must not exceed {prop}.max")
    return bounds or None


def _choices(spec, key, allowed):
    """Normalise a list of allowed labels; an empty list means no constraint."""
    values = spec.get(key) or []
    if isinstance(values, str):
        values = [values]
    values = [str(v).strip() for v in values if str(v).strip()]
    unknown = [v for v in values if v not in allowed]
    if unknown:
        raise InvalidSpecError(f"{key}: unknown {unknown}; expected one of {list(allowed)}")
    return values or None


def _nonneg_float(spec, key):
    if spec.get(key) in (None, ""):
        return None
    try:
        value = float(spec[key])
    except (TypeError, ValueError) as exc:
        raise InvalidSpecError(f"{key} must be a number") from exc
    if value < 0:
        raise InvalidSpecError(f"{key} must be zero or positive")
    return value


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
    if spec["max_ehull"] is not None:
        ehull = candidate.get("ehull")
        # Unknown stability cannot be shown to meet the limit, so it fails rather than passing silently.
        checks.append({"name": f"energy above hull <= {spec['max_ehull']} eV/atom",
                       "ok": ehull is not None and ehull <= spec["max_ehull"],
                       "detail": "no stability data" if ehull is None else f"{ehull:.3f}"})
    for prop in RANGE_PROPERTIES:
        bounds = spec.get(prop)
        if not bounds:
            continue
        entry = (candidate.get("properties") or {}).get(prop)
        value = None if entry is None else entry["value"]
        if "min" in bounds:
            checks.append({"name": f"{prop} >= {bounds['min']}",
                           "ok": value is not None and value >= bounds["min"],
                           "detail": "no data" if value is None else f"{value:.3f}"})
        if "max" in bounds:
            checks.append({"name": f"{prop} <= {bounds['max']}",
                           "ok": value is not None and value <= bounds["max"],
                           "detail": "no data" if value is None else f"{value:.3f}"})
    if spec["dimensionality"]:
        dim = candidate.get("dimensionality")
        checks.append({"name": f"dimensionality in {spec['dimensionality']}",
                       "ok": dim is not None and dim in spec["dimensionality"],
                       "detail": "no structure data" if dim is None else dim})
    if spec["crystal_system"]:
        system = candidate.get("crystal_system")
        checks.append({"name": f"crystal system in {spec['crystal_system']}",
                       "ok": system is not None and system in spec["crystal_system"],
                       "detail": "no structure data" if system is None else system})
    if spec["max_uncertainty"] is not None:
        checks.append({"name": f"uncertainty <= {spec['max_uncertainty']}", "ok": candidate["uncertainty"] <= spec["max_uncertainty"],
                       "detail": f"{candidate['uncertainty']:.3f}"})
    return {"satisfied": all(c["ok"] for c in checks), "checks": checks}
