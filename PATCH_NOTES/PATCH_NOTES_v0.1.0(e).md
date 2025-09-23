# Spectra App v0.1.0 (e) — Headerless ASCII heuristics

## Highlights
- Recover headerless and sparsely-labelled ASCII uploads by sniffing numeric columns when alias-based
  detection fails.
- Drop rows with invalid wavelength/flux pairs and surface the retained counts alongside detection
  strategy metadata in provenance for easier debugging.
- Align packaging metadata with PEP 440 using `0.1.0.dev5` so editable installs succeed again.

## Changes
- Rerun pandas parsing without headers when the first row is numeric, rename inferred columns, and fall
  back to monotonic/coverage heuristics to choose wavelength and flux arrays.
- Guard unit reporting so guessed wavelength columns emit `unknown` instead of placeholder labels and log
  the heuristic detection method, headerless flag, and row counts in provenance events.
- Expand regression coverage with a headerless CSV fixture to assert numeric inference, provenance
  annotations, and unit fallbacks.
- Updated ASCII ingest atlas documentation to describe the headerless retry, numeric heuristics, row
  filtering, and enriched provenance fields.
- Bump `pyproject.toml` to `0.1.0.dev5` and the app version badge to `0.1.0e` to unlock pip installs and
  satisfy release artifact verifiers.

## Verification
- `PYTHONPATH=. pytest -q`
- `python tools/verifiers/Verify-Atlas.py`
- `python tools/verifiers/Verify-PatchNotes.py`
- `python tools/verifiers/Verify-Handoff.py`
- `python tools/verifiers/Verify-Brains.py`
- `PYTHONPATH=. python tools/verifiers/Verify-UI-Contract.py`
