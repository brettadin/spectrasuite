# Spectra App v1.0.0 (f) — Unit-aware ASCII detection

## Highlights
- Teach the ASCII loader to inspect canonicalised units (µm/Å/cm⁻¹, erg/Jy/photons) when alias lookups
  fail so oddly-labelled exports still surface wavelength and flux arrays.
- Expand header sanitisation and alias token matching so BOM-prefixed, camel case, or suffixed columns like
  `Flux_Total` and `Noise` map cleanly to data and uncertainty channels.
- Align release artefacts with the 1.0.0f badge and bump packaging metadata to `1.0.0.dev6` while updating
  docs and regression coverage for the new heuristics.

## Changes
- Replaced simple alias equality checks with token-aware matching, broadened wavelength/flux/uncertainty
  synonym lists, and added unit-hint fallbacks before numeric heuristics.
- Canonicalised special unit glyphs (µ → `u`, Å → `angstrom`) and logged a new `unit_hint` provenance mode
  that captures when detection relied on units instead of column names.
- Added regressions for µm-based channels and cm⁻¹/photons exports to ensure the loader now recognises unit
  cues and propagates uncertainty columns.
- Updated the ASCII ingest atlas entry to describe the alias-token, unit-hint, and provenance enhancements.
- Bumped `pyproject.toml` to `1.0.0.dev6` and the UI badge to `1.0.0f` to keep packaging PEP 440 compliant
  while reflecting the new release cadence.

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
