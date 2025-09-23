# Spectra App v0.1.0 (b) — FITS ingestion

## Highlights
- Added FITS ingestion with header/WCS parsing, uncertainty support, and provenance logging.
- Extended canonicalisation to normalise FITS spectra onto the vacuum-nm baseline.
- Overlay tab uploader now accepts FITS files alongside ASCII uploads.

## Changes
- Implemented `server/ingest/fits_loader.py` with metadata harvesting, SHA-256 dedupe hash, and
  WCS-aware wavelength grids.
- Introduced `canonicalize_fits` plus reusable wavelength-unit normalisation in
  `server/ingest/canonicalize.py`.
- Updated the Streamlit overlay flow to route FITS files through the new ingest path and surface
  mixed-type uploads without duplicates.
- Added regression tests for FITS ingestion and air↔vacuum conversion; seeded a sample FITS file in
  `data/examples/`.
- Refreshed documentation/atlas entries and version metadata for v0.1.0b.

## Known Issues
- Archive fetchers (MAST/SDSS) remain stubbed; Star Hub lists resolver results only.
- Replay script still limited to canonical spectra reconstruction; UI rebuild CLI pending.
- Performance optimisations (async ingest, LOD) are outstanding.

## Verification
- `ruff check . --fix`
- `black .`
- `mypy .`
- `pytest`
- `python tools/verifiers/Verify-Atlas.py`
- `python tools/verifiers/Verify-Brains.py`
- `python tools/verifiers/Verify-PatchNotes.py`
- `python tools/verifiers/Verify-Handoff.py`
- `python tools/verifiers/Verify-UI-Contract.py`
