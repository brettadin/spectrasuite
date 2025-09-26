# HANDOFF 1.0.0o — Similarity analysis restoration

## 1) Summary of This Run
- Reintroduced the overlay similarity analysis with configurable metrics, viewport selection, and
  reference trace controls.
- Added a reusable similarity engine (`server/analysis/similarity.py`) plus regression tests covering
  normalization, cache symmetry, and viewport alignment.
- Updated documentation/metadata (atlas, patch notes, brains, version) to reflect the feature return.

## 2) Current State of the Project
- **Working tabs:** Overlay (now with similarity controls), Differential, Star Hub, Docs.
- **Data ingestion:** ASCII/FITS canonicalisation to vacuum nm with provenance; archive downloads flow
  through `ingest_product` with metadata guards.
- **Similarity:** Visible traces feed the new similarity panel with metric selection, normalization, and
  optional manual viewport.
- **Docs & comms:** Patch notes / brains / version metadata updated for v1.0.0o.

## 3) Next Steps (Prioritized)
1. Persist similarity configuration (metrics, viewport, reference) into export manifests for replay.
2. Investigate adaptive downsampling so similarity remains performant with >15k-point traces.
3. Enhance line-match scoring with line catalog metadata (weights, identifications).

## 4) Decisions & Rationale
- Limited similarity inputs to 15k points per trace for now to keep unions manageable until smarter
  decimation is implemented.
- Cached metric computations by fingerprint + viewport to avoid recomputation when toggling metrics.
- Surfaced similarity in-tab (no extra tab) to preserve the UI contract established in the refactor.

## 5) References
- Patch notes: `PATCH_NOTES/PATCH_NOTES_v1.0.0(o).md`
- Brains log: `brains/v1.0.0o__assistant__similarity_panel.md`
- Atlas: `atlas/ui_contract.md`

## 6) Quick Start for the Next AI
- Install deps / smoke: `python -m pip install -e .`, `PYTHONPATH=. pytest -q`.
- Static checks: `ruff check .`, `black --check .`, `mypy .`.
- Verifiers: `python tools/verifiers/Verify-Atlas.py`, `Verify-PatchNotes.py`, `Verify-Brains.py`,
  `Verify-Handoff.py`, `PYTHONPATH=. python tools/verifiers/Verify-UI-Contract.py`.
- Manual QA: Load two spectra (ASCII or FITS), toggle visibility, adjust similarity viewport/metrics,
  confirm ribbon/matrix refresh, and export the session (export still omits similarity config).
