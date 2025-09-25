# Spectra App v1.0.0 (n) — Archive metadata resilience

## Highlights
- Hardened archive ingestion so spectra missing canonical metadata no longer crash the merge step.
- Added regression coverage ensuring placeholder canonical spectra gain proper metadata during ingestion.
- Advanced version metadata to `1.0.0n` / `1.0.0.dev14` for this stabilization patch.

## Changes
- Guarded `ingest_product` metadata merging to initialise a `TraceMetadata` stub when absent and to
  tolerate missing source hashes when checking placeholder IDs.
- Extended the ingestion test suite with coverage for metadata-free canonical spectra to prevent
  regressions of the observed crash.
- Bumped version identifiers in `pyproject.toml` and `app/config/version.json` to signal the fix.

## Known Issues
- Archive fetches still depend on network access; consider cached fixtures for offline validation.
- Full citation/DOI propagation remains pending richer mission metadata cataloguing.
- Export manifest replay work continues to track archive download URIs.

## Verification
- `python -m pip install -e .`
- `ruff check .`
- `black --check .`
- `mypy .`
- `PYTHONPATH=. pytest -q`
- `python tools/verifiers/Verify-Atlas.py`
- `python tools/verifiers/Verify-PatchNotes.py`
- `python tools/verifiers/Verify-Brains.py`
- `python tools/verifiers/Verify-Handoff.py`
- `PYTHONPATH=. python tools/verifiers/Verify-UI-Contract.py`
