# Spectra App v1.0.0 (j) — Axis provenance in the UI

## Highlights
- Surface the interpreted axis family directly in the Overlay trace manager so uploads reveal whether
  they were treated as wavelength, wavenumber, frequency, or energy without digging into exports.
- Include the detection method, source column, and unit context alongside the axis badge to accelerate
  debugging messy headers and headerless ingests.

## Changes
- Added axis-summary helpers to the Overlay tab that inspect provenance events and render a caption per
  trace covering axis family, units, detection method, and headerless fallbacks for ASCII and FITS data.
- Expanded the test suite with coverage for ASCII alias, headerless heuristics, and FITS ingestion to
  ensure the new helpers report the correct axis metadata.
- Bumped repository metadata to advertise `1.0.0j` / `1.0.0.dev10` and refreshed docs, brains, and the
  handoff log to describe the new UI provenance feature.

## Known Issues
- Archive fetchers (MAST/SDSS) remain stubbed; Star Hub still relies on fixtures.
- Replay CLI/UI reconstruction tooling still pending, and Docs tab needs expansion beyond the current
  overview content.
- Axis provenance is shown inline per trace, but a richer history browser for downstream transforms
  remains on the roadmap.

## Verification
- `python -m pip install -e .`
- `ruff check .`
- `black --check .`
- `mypy .`
- `PYTHONPATH=. pytest -q`
- `python tools/verifiers/Verify-Atlas.py`
- `python tools/verifiers/Verify-PatchNotes.py`
- `python tools/verifiers/Verify-Handoff.py`
- `python tools/verifiers/Verify-Brains.py`
- `PYTHONPATH=. python tools/verifiers/Verify-UI-Contract.py`
