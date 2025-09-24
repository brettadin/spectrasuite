# HANDOFF 1.0.0f — Unit-aware ASCII detection
## 1) Summary of This Run
- Extended ASCII ingestion to match aliases token-wise and consult canonicalised units (µm/Å/cm⁻¹,
  erg/Jy/photons) before numeric fallbacks so oddly-labelled exports now ingest without manual tweaks.
- Normalised micro/angstrom glyphs, broadened uncertainty synonyms (`noise`, `rms`, `stddev`), and surfaced a
  new `unit_hint` provenance mode for transparency when units drove detection.
- Added regressions for µm and cm⁻¹/photons datasets, refreshed atlas guidance, and bumped release metadata
  to `1.0.0f` / `1.0.0.dev6` to match the 1.0 cadence.

## 2) Current State of the Project
- **Working tabs:** Overlay (ASCII+FITS with alias/unit heuristics), Differential, Star Hub (SIMBAD), Line
  Atlas, Upload history with enriched provenance logging.
- **Data ingestion:** FITS loader unchanged; ASCII loader now handles BOMs, messy headers, bare numerics, and
  unit-driven column detection.
- **Docs & comms:** Atlas, patch notes, brains journal, and this handoff updated for v1.0.0f.

## 3) Next Steps (Prioritized)
1. Gather additional real-world exports (energy/frequency axes, alternate flux units) to extend the unit hint
   lists without introducing false positives.
2. Explore heuristics for uncertainty units or numeric fallbacks once representative samples appear.
3. Continue migrating historical 0.1.x artefacts to 1.0.x naming to reduce confusion in release archives.

## 4) Decisions & Rationale
- Alias detection now compares token sets so suffixed/prefixed labels (`Flux_Total`, `Noise_Level`) still map
  correctly while short aliases (`nm`, `um`, `aa`) remain exact to avoid collisions.
- Unit hints are only applied when alias lookups fail, and provenance records `unit_hint` vs `numeric_heuristic`
  so support can see which path triggered.
- Retaining the provided unit string (e.g., `µm`, `cm^-1`) keeps downstream plots accurate, while numeric
  fallbacks still label wavelength units as `unknown` to avoid placeholder leakage.
- Bumping to `1.0.0.dev6` keeps packaging compliant with PEP 440 while aligning the UI badge with the 1.0.0f
  release requested by the team.

## 5) References
- Atlas: `atlas/ingest_ascii.md` (alias tokens, unit hints, provenance updates)
- Patch notes: `PATCH_NOTES/PATCH_NOTES_v1.0.0(f).md`
- Brains log: `brains/v1.0.0f__assistant__ascii_unit_hints.md`

## 6) Quick Start for the Next AI
- Install deps / run smoke: `python -m pip install -e .`, `PYTHONPATH=. pytest -q`.
- Static checks: `ruff check .`, `black --check .`, `mypy .`.
- Verifiers: `python tools/verifiers/Verify-Atlas.py`, `Verify-PatchNotes.py`, `Verify-Brains.py`,
  `Verify-Handoff.py`, `PYTHONPATH=. python tools/verifiers/Verify-UI-Contract.py`.
- Manual QA: upload µm- or cm⁻¹-labelled CSVs to confirm detection_method=`unit_hint` and verify provenance
  reports retained row counts plus the resolved units.
