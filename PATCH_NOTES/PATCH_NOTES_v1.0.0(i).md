# Spectra App v1.0.0 (i) — High-energy axis support

## Highlights
- Extend ASCII ingestion to recognise keV/MeV energy axes so high-energy exports land on the wavelength
  baseline without manual remapping.
- Add petahertz frequency conversions alongside lower-frequency scales for uploads spanning UV/X-ray
  regimes.
- Record the detected axis family (wavelength, wavenumber, frequency, energy) in provenance to simplify
  debugging and provenance audits.

## Changes
- Expanded `server/math/transforms.py` with nm↔frequency_phz and nm↔energy_{keV,MeV} helpers plus updated
  canonicalisation maps.
- Broadened ASCII unit hints to cover keV/MeV/PHz, classified axis families during ingest, and added test
  coverage for the new units and provenance field.
- Refreshed atlas/docs, brains journal, patch notes, handoff, and metadata to advertise `1.0.0i` /
  `1.0.0.dev9`.

## Known Issues
- Archive fetchers (MAST/SDSS) remain stubbed; Star Hub continues to rely on fixtures.
- Replay CLI/UI reconstruction tooling still pending, and docs tab needs expansion beyond the current
  overview content.
- Axis-family provenance is available via exports but is not yet surfaced explicitly in the UI.

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
