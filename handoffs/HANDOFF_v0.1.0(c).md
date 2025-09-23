# HANDOFF 0.1.0c — FITS multi-extension ingestion
## 1) Summary of This Run
- Extended FITS ingest to support spectra with companion wavelength extensions and inverse-variance
  uncertainties, converting them into the canonical model with provenance preserved.
- Added a specutils-based fallback path for non-linear/tabular WCS solutions and captured which path
  produced the dispersion axis so replay tooling can mirror the decision.
- Updated regression tests, atlas documentation, and version metadata for v0.1.0c.

## 2) Current State of the Project
- **Working tabs:** Overlay (ASCII+FITS with multi-extension + specutils fallback), Differential,
  Star Hub (SIMBAD resolver with fixtures), Docs.
- **Known gaps:** Archive fetchers (MAST/SDSS) remain stubbed; replay CLI/UI reconstruction still
  pending; docs tab still a high-level placeholder.
- **Performance:** Adequate for sample traces; specutils fallback adds overhead for complex FITS but
  runs only when native parsing fails.
- **Debt:** Archive adapters, replay automation, richer docs/accessibility review, and ingest
  performance profiling/caching.

## 3) Next Steps (Prioritized)
1) Implement `server/fetchers/mast.py` and `server/fetchers/sdss.py` with fixture-backed tests that
   exercise metadata/provenance paths.
2) Build the export replay CLI/UI reconstruction tooling to honour provenance (including specutils
   fallback indicators).
3) Profile specutils fallback performance and investigate caching or format hints for bulk ingest
   workloads.

## 4) Decisions & Rationale
- Prioritised native FITS parsing and only invoked specutils when dispersion information is missing to
  keep the common path lightweight while still supporting complex archives.
- Normalised inverse-variance (`ivar`) arrays into σ to align with existing numerical safeguards and
  uncertainty propagation rules.
- Recorded provenance for both companion HDU resolution and specutils fallback so manifest replay can
  reconstruct the ingest flow deterministically.

## 5) References
- Atlas: `atlas/ingest_fits.md`
- Brains: `brains/v0.1.0c__assistant__fits_wcs.md`
- Patch notes: `PATCH_NOTES/PATCH_NOTES_v0.1.0(c).md`
- Tests: `tests/test_fits_loader.py`

## 6) Quick Start for the Next AI
- Install: `pip install -e .[dev]`
- Run app: `streamlit run app/app_patched.py`
- Quality gates: `ruff check . --fix`, `black .`, `mypy .`, `python -m pytest`, then
  `python tools/verifiers/Verify-*.py`
- Sample data: ASCII (`data/examples/example_spectrum.csv`), single-HDU FITS (`data/examples/example_spectrum.fits`),
  plus tests generate SDSS-like fixtures on demand.
