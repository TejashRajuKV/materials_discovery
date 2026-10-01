"""Thermodynamic stability layer.

Honest placeholder: the current dataset has no formation energy / energy-above-hull
data, so stability cannot be assessed. The layer reports `not_assessed` instead of
inventing a score. Implement once a dataset with stability labels is adopted.
"""


def validate_stability(formula):
    return {
        "layer": "stability",
        "status": "not_assessed",
        "checks": [{"name": "energy_above_hull", "ok": None, "detail": "no stability data in current dataset"}],
    }
