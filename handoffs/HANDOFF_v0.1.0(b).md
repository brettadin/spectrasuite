# HANDOFF 0.1.0b — FITS ingestion groundwork
## 1) Summary of This Run
- Implemented FITS ingestion with WCS-based wavelength reconstruction, uncertainty harvesting, and
  provenance logging. Added `canonicalize_fits` to map FITS spectra onto the vacuum-nm baseline.
- Updated the Overlay tab uploader to accept FITS files alongside ASCII, leveraging dedupe logic and
  producing success/warning messaging for mixed uploads.
- Seeded a representative FITS example, expanded atlas/docs/readme, bumped version metadata to
  0.1.0b, and refreshed continuity artefacts.

## 2) Current State of the Project
- **Working tabs:** Overlay (ASCII+FITS ingest, line overlays, export), Differential (A−B/A/B ops),
  Star Hub (SIMBAD resolver with fixture fallback), Docs (overview placeholder).
- **Known gaps:** FITS ingest handles linear dispersion/WCS tables; more complex WCS solutions and
  archive fetchers (MAST/SDSS) remain stubbed. Replay CLI/UI reconstruction still pending.
- **Performance:** Plotly Scattergl remains responsive for sample traces; async ingest & LOD not yet
  implemented.
- **Debt:** Star Hub provider adapters, replay automation, richer docs/accessibility review, and
  performance benchmarking.

## 3) Next Steps (Prioritized)
1) `server/ingest/fits_loader.py`: extend to support multi-extension tables (flux+wave separated) and
   non-linear WCS by leaning on `specutils.Spectrum1D`. Acceptance: ingest SDSS-style FITS sample and
   populate provenance/metadata correctly.
2) `server/fetchers/mast.py` & `server/fetchers/sdss.py`: implement adapters with cached fixtures and
   unit tests exercising manifest metadata (product IDs, wavelengths, DOIs).
3) `server/export/manifest.py` + new CLI module: finish replay pipeline to rebuild session state from
   manifest JSON, including overlays and axis unit/display mode restoration.

## 4) Decisions & Rationale
- Recorded a concise set of WCS keywords plus SHA-256 hash in provenance to keep manifests portable
  without bloating export size with full headers.
- Mapped frame hints via `SPECSYS` header to canonical enums (topocentric/heliocentric/barycentric)
  to prime downstream RV/frame tools.
- Display warning for unsupported upload suffixes to avoid implicit fallbacks that could bypass
  provenance logging.

## 5) References
- Atlas files updated: /atlas/ingest_fits.md, /atlas/README.md
- Brains file for this run: /brains/v0.1.0b__assistant__fits_ingest.md
- Patch notes: /PATCH_NOTES/PATCH_NOTES_v0.1.0(b).md
- Related tests: /tests/test_fits_loader.py

## 6) Quick Start for the Next AI
- Install: `pip install -e .[dev]`
- Run app: `streamlit run app/app_patched.py`
- Quality gates: `ruff check . --fix`, `black .`, `mypy .`, `pytest`, then `python tools/verifiers/Verify-*.py`
- Sample data: ASCII (`data/examples/example_spectrum.csv`) and FITS (`data/examples/example_spectrum.fits`)
  cover loader smoke tests; SIMBAD fixture lives at `data/examples/simbad_m31.json`.
