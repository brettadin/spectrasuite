# Spectra App v1.0.0 (h) — Frequency & energy ingestion

## Highlights
- Expand ASCII ingestion to recognise frequency (Hz/THz) and energy (eV) axes so spectra exported
  in those domains resolve to wavelength without manual relabelling.
- Add conversion utilities for frequency and energy units, enabling canonical nm baselines for
  the new ingestion paths and future UI toggles.
- Refresh documentation, patch notes, and metadata to advertise `1.0.0h` / `1.0.0.dev8`.

## Changes
- Broaden wavelength alias and unit-hint vocabularies to prioritise frequency/energy headers,
  using unit hints when labels are generic so CSVs with `Axis (THz)` or `PhotonEnergy (eV)` map
  to wavelength before canonicalisation.
- Extend `server/math/transforms.py` with Hz↔nm and eV↔nm helpers plus round-trip coverage,
  plumbing the new unit types through canonicalisation.
- Add regression tests for frequency/energy ingestion and the associated conversions alongside
  documentation updates across the atlas and docs overview.

## Known Issues
- Archive fetchers (MAST/SDSS) remain stubbed; Star Hub continues to rely on fixtures.
- Replay CLI/UI reconstruction tooling still pending, and docs tab needs expansion beyond the
  current overview content.
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
