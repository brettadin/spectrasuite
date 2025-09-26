# Spectra App v1.0.0 (o) — Similarity analysis revival

## Highlights
- Reintroduced the overlay similarity analysis with configurable metrics, normalization, and viewport controls.
- Added a reusable similarity engine module with caching plus regression tests for metric stability.
- Documented the overlay UI contract update and bumped release metadata to `1.0.0o` / `1.0.0.dev15`.

## Changes
- Ported the legacy similarity algorithms into `server/analysis/similarity.py` and exposed a Streamlit panel in the overlay tab.
- Wired new controls for metric selection, viewport bounds, and reference trace selection while preserving existing overlay layout.
- Added `tests/test_similarity.py` to exercise normalization, caching symmetry, and matrix construction.
- Updated `atlas/ui_contract.md`, patch/brain/handoff notes, and version metadata for the feature return.

## Known Issues
- Similarity calculations still operate on downsampled canonical grids; adaptive binning for extremely dense spectra remains future work.
- Line-match scoring relies on simple peak distance heuristics and does not yet weight by line metadata.
- Export manifests do not yet persist similarity configuration for replay.

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
