# Spectra App v0.1.0 (a) — Bootstrap

## Highlights
- First runnable Streamlit interface with Overlay, Differential, Star Hub, and Docs tabs.
- Canonical ingestion pipeline for ASCII spectra with provenance logging and deduplication.
- Export bundle delivering manifest v2, per-trace CSVs, and optional PNG snapshot.
- SIMBAD resolver integration (with offline fallback) and Fe I line overlay catalogue.

## Changes
- Implemented session state, unit toggles (nm/Å/µm/cm⁻¹), and line overlay controls.
- Added numerical engines for wavelength/unit transforms, resolution matching, and differential analyses.
- Populated `/tools/verifiers` and CI workflow to enforce atlas/brains/notes/handoff updates and UI contract.
- Seeded example data, docs placeholders, and atlas documentation for every subsystem.

## Known Issues
- FITS ingestion and external archive adapters (MAST/SDSS) are stubbed pending future runs.
- Export replay helper is limited to canonical spectra; UI reconstruction will be expanded.

## Verification
- `ruff check . --fix`
- `black .`
- `mypy .`
- `pytest`
