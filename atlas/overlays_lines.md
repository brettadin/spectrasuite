# Line Overlays

- Catalog: `LineCatalog` loads CSV fixtures (currently Fe I NIST-inspired sample) and exposes
  species list + per-species entries.
- Scaling: `scale_lines` supports `relative` (max-normalised) and `quantile` (P99 normalised) modes
  with optional gamma exponent and relative threshold filter.
- Velocity: `apply_velocity_shift` uses doppler shift helper to align overlays with RV adjustments.
- UI: sidebar controls drive species, mode, gamma, threshold, Δv; overlay plotted on secondary y-axis
  with lollipop-style traces.
