# HANDOFF 1.0.0g — Error-aware ASCII ingestion
## 1) Summary of This Run
- Hardened ASCII ingestion so uncertainty-prefixed headers (e.g., `Flux_Error`, `Wavelength_Error`) no longer win
  alias detection, keeping wavelength/flux arrays pointed at the science columns even when files list errors first.
- Detected and excluded uncertainty columns before alias/unit-hint/numeric fallbacks, prioritising flux-style
  errors when exposing an uncertainty array, and widened the flux synonyms to cover signal/reflectance/transmission
  exports.
- Added regression coverage for error-first CSVs, documented the safeguards in the atlas, and bumped metadata to
  `1.0.0g` / `1.0.0.dev7` alongside refreshed patch notes and brains log.

## 2) Current State of the Project
- **Working tabs:** Overlay (ASCII+FITS with error-aware detection), Differential, Star Hub (SIMBAD), Line Atlas,
  Upload history with provenance capturing detection method, retained rows, and content hash.
- **Data ingestion:** FITS loader unchanged; ASCII loader now handles messy headers, unit hints, headerless data,
  and disambiguates uncertainty columns before resolving wave/flux.
- **Docs & comms:** Atlas, patch notes, brains journal, and this handoff updated for v1.0.0g.

## 3) Next Steps (Prioritized)
1. Gather additional exports using frequency/energy axes to extend preferred-token lists and unit conversions.
2. Consider promoting wavelength-error columns into provenance metadata for richer diagnostics without treating
   them as numeric axes.
3. Continue auditing historical release artefacts to reconcile 0.1.x vs 1.0.x naming for clarity.

## 4) Decisions & Rationale
- Score-based alias matching keeps behaviour deterministic while letting us penalise uncertainty tokens instead of
  hard-coding exclusion lists.
- Detecting uncertainties first avoids flux misclassification without losing the ability to propagate error bars
  when available.
- Maintaining the 1.0.0 cadence with `1.0.0.dev7` preserves PEP 440 compliance and aligns the badge with release
  communications.

## 5) References
- Atlas: `atlas/ingest_ascii.md` (error-channel guardrails)
- Patch notes: `PATCH_NOTES/PATCH_NOTES_v1.0.0(g).md`
- Brains log: `brains/v1.0.0g__assistant__ascii_error_filter.md`

## 6) Quick Start for the Next AI
- Install deps / smoke: `python -m pip install -e .`, `PYTHONPATH=. pytest -q`.
- Static checks: `ruff check .`, `black --check .`, `mypy .`.
- Verifiers: `python tools/verifiers/Verify-Atlas.py`, `Verify-PatchNotes.py`, `Verify-Brains.py`,
  `Verify-Handoff.py`, `PYTHONPATH=. python tools/verifiers/Verify-UI-Contract.py`.
- Manual QA: upload CSVs with `Flux_Error`/`Wavelength_Error` leading the header row and confirm provenance reports
  the primary columns, the uncertainty column is optional, and the plot displays the expected curves.
