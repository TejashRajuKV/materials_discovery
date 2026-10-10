"""Thermodynamic stability layer, from energy above the convex hull (`ehull`, eV/atom).

ehull is 0 for a stable compound and grows with how far it sits above the hull. Only materials
with a JARVIS entry have a value, so generated candidates report `not_assessed` rather than a
guessed score. Thresholds are conventions, not physics; change them here if needed.
"""
PASS_EHULL = 0.025  # eV/atom: at or below this, treated as on or very near the hull

# The layer informs but does not exclude by default: most JARVIS entries are above the hull, and
# excluding them all would change every discovery result. Hard limits come from the `max_ehull`
# requirement, which is evaluated as a constraint.


def validate_stability(prediction):
    ehull = prediction.get("ehull")
    if ehull is None:
        return {
            "layer": "stability",
            "status": "not_assessed",
            "checks": [{"name": "energy_above_hull", "ok": None,
                        "detail": "no JARVIS entry for this composition; stability is unknown"}],
        }
    on_hull = ehull <= PASS_EHULL
    return {
        "layer": "stability",
        "status": "pass" if on_hull else "warn",
        "checks": [{"name": f"energy_above_hull <= {PASS_EHULL} eV/atom", "ok": on_hull,
                    "detail": f"{ehull:.3f} eV/atom"}],
    }
