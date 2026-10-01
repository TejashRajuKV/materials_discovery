# Scientific background

- **Band gap**: energy gap between valence and conduction bands; separates metals (≈0 eV),
  semiconductors and insulators. Central to photovoltaics, LEDs, transparent conductors.
- **Composition-based ML**: element-property statistics (Magpie-style; Ward et al., 2016) turn a
  formula into a fixed-length vector usable by classical regressors. Used here because the MVP
  dataset has formulas only.
- **Why not "accuracy"**: scientific regression is judged by MAE/RMSE/R², error *by regime*
  (metals vs. wide-gap), and by generalisation to unseen chemistries — hence grouped splits.
- **Prediction ≠ synthesisability**: an ML estimate says nothing about stability or whether a
  compound can be made. The platform therefore keeps validation layers separate and labels
  unassessed ones (`stability` is *not assessed* until stability data is available).
