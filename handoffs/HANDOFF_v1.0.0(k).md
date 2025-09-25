# HANDOFF 1.0.0k — Transform provenance surfaced in UI

## 1) Summary of This Run
- Overlay trace manager now lists downstream provenance (unit conversions, air→vacuum steps, differential
  operations) alongside the axis-family captions so analysts can audit transforms without exporting.
- Regression coverage exercises the new transform notes for air-wavelength ASCII uploads and derived
  differential spectra to keep the UI summaries trustworthy.
- Documentation, patch notes, brains log, and metadata advertise `1.0.0k` / `1.0.0.dev11` and describe
  the expanded provenance display.

## 2) Current State of the Project
- **Working tabs:** Overlay (axis and transform provenance captions, line overlays, export), Differential,
  Star Hub (SIMBAD resolver placeholder), Line Atlas, Docs.
- **Data ingestion:** ASCII/FITS loaders classify axis family, detect air vs vacuum, and log provenance
  events consumed by the UI transform summaries.
- **Docs & comms:** Atlas UI contract, overview doc, patch notes, brains log, and this handoff reflect the
  new UI provenance behaviour.

## 3) Next Steps (Prioritized)
1. Extend provenance display once additional transforms (e.g., resolution matching) emit events.
2. Continue archive fetcher build-out so real products exercise the enhanced UI provenance trail.
3. Expand Docs tab content with troubleshooting guidance referencing the new captions.

## 4) Decisions & Rationale
- Reused existing provenance event payloads, avoiding schema changes and ensuring historical traces gain
  UI visibility immediately.
- Rendered transform notes inline with axis captions to keep context close to the visibility toggles used
  during analysis sessions.
- Formatted epsilon parameters succinctly so long differential chains remain readable in the sidebar.

## 5) References
- Patch notes: `PATCH_NOTES/PATCH_NOTES_v1.0.0(k).md`
- Brains log: `brains/v1.0.0k__assistant__transform_provenance_ui.md`
- Atlas: `atlas/ui_contract.md`

## 6) Quick Start for the Next AI
- Install deps / smoke: `python -m pip install -e .`, `PYTHONPATH=. pytest -q`.
- Static checks: `ruff check .`, `black --check .`, `mypy .`.
- Verifiers: `python tools/verifiers/Verify-Atlas.py`, `Verify-PatchNotes.py`, `Verify-Brains.py`,
  `Verify-Handoff.py`, `PYTHONPATH=. python tools/verifiers/Verify-UI-Contract.py`.
- Manual QA: upload Angstrom-labelled ASCII files or compute differentials and confirm the transform
  caption lists conversions, air→vacuum corrections, and differential operations inline beneath the trace.
