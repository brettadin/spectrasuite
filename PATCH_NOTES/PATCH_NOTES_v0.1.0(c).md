# Spectra App v0.1.0 (c) — FITS multi-extension support

## Highlights
- Extended FITS ingest to read spectra with separate wavelength extensions and inverse-variance
  uncertainties while preserving provenance.
- Added a specutils-powered fallback for non-linear or tabular wavelength solutions so SDSS-style
  products ingest without manual WCS decoding.
- Updated regression coverage, documentation, and version metadata for v0.1.0c.

## Changes
- Enhanced `server/ingest/fits_loader.py` with companion HDU discovery, `ivar` → σ conversion,
  and a specutils fallback pipeline that captures provenance when non-linear WCS handling is
  delegated externally.
- Added regression tests for multi-extension FITS payloads and specutils-driven ingestion in
  `tests/test_fits_loader.py`.
- Documented the new capabilities in `atlas/ingest_fits.md` and bumped package/config versions to
  `0.1.0c`.

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
