"""Chemical plausibility checks on a composition."""
from ml.representation.material_representation import InvalidMaterialError, parse_formula

NOBLE_GASES = {"He", "Ne", "Ar", "Kr", "Xe", "Rn"}


def validate_composition(formula):
    """Return a layer result: {status: pass|warn|fail, checks: [...]}."""
    checks = []
    try:
        comp = parse_formula(formula)
    except InvalidMaterialError as exc:
        return {"layer": "chemical", "status": "fail", "checks": [{"name": "parsable", "ok": False, "detail": str(exc)}]}
    checks.append({"name": "parsable", "ok": True, "detail": comp.reduced_formula})

    symbols = {e.symbol for e in comp.elements}
    noble = symbols & NOBLE_GASES
    checks.append({"name": "no_noble_gases", "ok": not noble, "detail": ", ".join(sorted(noble)) or "none"})

    heavy = [e.symbol for e in comp.elements if e.Z > 83]
    checks.append({"name": "no_radioactive_heavy_elements", "ok": not heavy, "detail": ", ".join(heavy) or "none"})

    try:
        guesses = comp.oxi_state_guesses()
    except Exception:
        guesses = []
    balanced = bool(guesses)
    checks.append({
        "name": "charge_balanced",
        "ok": balanced,
        "detail": ", ".join(f"{k}{v:+g}" for k, v in guesses[0].items()) if balanced else "no charge-neutral oxidation-state assignment",
    })

    hard_fail = (not checks[1]["ok"]) or (not checks[2]["ok"])
    status = "fail" if hard_fail else ("pass" if balanced else "warn")
    return {"layer": "chemical", "status": status, "checks": checks}
