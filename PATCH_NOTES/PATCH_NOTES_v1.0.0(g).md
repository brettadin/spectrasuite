# Spectra App v1.0.0 (g) — Error-aware ASCII ingestion

## Highlights
- Prevent wavelength and flux detection from grabbing trailing `*_error`/`*_sigma` columns so uploads with
  leading uncertainty fields no longer fail or plot the wrong axis.
- Prioritise flux-related error channels when deriving uncertainties and widen the alias map to cover signal,
  reflectance, transmission, and throughput style datasets.
- Document the error-channel guardrails in the ASCII ingest atlas and advance the release metadata to
  `1.0.0g` / `1.0.0.dev7`.

## Changes
- Score alias matches by token quality, penalising uncertainty tokens and boosting preferred flux/wave
  vocab so that `Flux_Error`/`Wavelength_Error` no longer win over their primary counterparts.
- Detect uncertainty columns before wave/flux resolution and exclude them from alias, unit-hint, and numeric
  fallbacks to keep heuristics focused on the data axes while still propagating flux uncertainties.
- Broaden the flux alias set (signal, reflectance, transmission, absorbance, throughput) and add tests that
  cover error-prefixed headers to guarantee provenance points at the right columns.
- Updated `atlas/ingest_ascii.md`, patch notes, brains log, and handoff to describe the new safeguards and
  bumped version metadata to `1.0.0g` / `1.0.0.dev7`.

## Known Issues
- Archive fetchers (MAST/SDSS) remain stubbed; Star Hub continues to rely on fixtures.
- Replay CLI/UI reconstruction tooling still pending, and docs tab needs expansion beyond the current
  overview content.
- Performance investigations for bulk ingest and async pipelines remain on the roadmap.

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
