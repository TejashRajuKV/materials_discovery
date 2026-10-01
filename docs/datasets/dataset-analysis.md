# Dataset analysis (synthetic demo set)

- 2,500 generated rows → 2,499 after cleaning (1 unparsable formula dropped); no duplicates.
- Target: mean 1.41 eV, std 1.56, max 8.1 eV; **29.6 % exactly 0** (a zero-inflated target — MAPE is
  computed on non-zero targets only).
- Chemistry: 1–2 cations + 1 anion from a fixed pool; charge-balanceable only.

## Limitations
1. Synthetic labels: the "signal" is a function of electronegativity, which is also a model
   feature — so the high R² is expected and says nothing about real materials.
2. Narrow chemistry (≤ 3 elements, one anion) — real databases are far broader.
3. No structures, polymorphs, or stability labels.

Rewrite this document once a real dataset is adopted.
