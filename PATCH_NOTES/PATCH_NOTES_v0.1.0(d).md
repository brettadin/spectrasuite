# Spectra App v0.1.0 (d) — Resilient ASCII uploads

## Highlights
- Normalised ASCII header tokens so uploads with mixed casing, camel case, or punctuation variants
  still detect wavelength, flux, and metadata fields automatically.
- Expanded metadata synonym detection (Target/Object/Instrument/Telescope/Observer) and filtered
  null-like values to keep provenance clean while deriving display labels reliably.
- Added regression coverage for messy header combinations and bumped version metadata to 0.1.0d.

## Changes
- Hardened `server/ingest/ascii_loader.py` with canonical header tokenisation, richer alias sets,
  and smarter metadata extraction/label inference so "FluxDensity", "Wave Length", etc. parse
  correctly.
- Added regression test `tests/test_ascii_loader.py::test_ascii_loader_handles_messy_synonyms` to
  lock in support for the broadened alias detection.
- Documented the ingestion changes in `atlas/ingest_ascii.md` and updated version artifacts to
  `0.1.0d`.

## Known Issues
- Archive fetchers (MAST/SDSS) remain stubbed; Star Hub continues to rely on fixtures.
- Replay CLI/UI reconstruction tooling still pending, and docs tab needs expansion beyond the
  current overview content.
- Performance investigations for bulk ingest and async pipelines remain on the roadmap.

## Verification
- `ruff check .`
- `black --check .`
- `mypy .`
- `PYTHONPATH=. pytest -q`
- `python tools/verifiers/Verify-Atlas.py`
- `python tools/verifiers/Verify-Brains.py`
- `python tools/verifiers/Verify-PatchNotes.py`
- `python tools/verifiers/Verify-Handoff.py`
- `PYTHONPATH=. python tools/verifiers/Verify-UI-Contract.py`
