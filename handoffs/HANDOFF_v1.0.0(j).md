# HANDOFF 1.0.0j — Axis provenance surfaced in UI

## 1) Summary of This Run
- Overlay trace manager now displays the detected axis family, source column, unit, and detection method
  for each trace so analysts can confirm whether uploads were treated as wavelength, wavenumber,
  frequency, or energy at a glance.
- Added regression coverage for ASCII alias/headerless ingests and FITS spectra to ensure the provenance
  summary stays accurate as the loaders evolve.
- Updated documentation, patch notes, brains log, and metadata to advertise `1.0.0j` / `1.0.0.dev10` with
  the new UI provenance feature.

## 2) Current State of the Project
- **Working tabs:** Overlay (ASCII/FITS ingest with axis summaries, line overlays, export), Differential,
  Star Hub (SIMBAD), Line Atlas, Docs, upload history with provenance capturing detection method,
  retained rows, axis family, and content hash.
- **Data ingestion:** ASCII loader handles wavelength, wavenumber, frequency (Hz→PHz), and energy
  (eV/keV/MeV) axes with uncertainty filtering; FITS loader unchanged.
- **Docs & comms:** Atlas UI contract, patch notes, brains log, overview doc, and this handoff capture the
  new axis provenance UI.

## 3) Next Steps (Prioritized)
1. Extend the provenance display to downstream transforms (air↔vacuum, resolution matching, differentials)
   for fuller audit trails inside the UI.
2. Continue archive fetcher build-out so high-energy and frequency products from MAST/SDSS exercise the
   new axis provenance summaries.
3. Expand Docs tab content with workflow guidance and legal/data-source acknowledgements.

## 4) Decisions & Rationale
- Reused existing `ingest_*` provenance events to populate the UI, avoiding metadata migrations and
  benefiting historical uploads immediately.
- Chose inline captions beneath each trace checkbox to keep the information close to visibility controls
  without introducing new layout chrome.
- Included detection method and headerless hints so analysts can quickly diagnose why a column was chosen
  or whether numeric heuristics fired.

## 5) References
- Patch notes: `PATCH_NOTES/PATCH_NOTES_v1.0.0(j).md`
- Brains log: `brains/v1.0.0j__assistant__axis_provenance_ui.md`
- Atlas: `atlas/ui_contract.md`

## 6) Quick Start for the Next AI
- Install deps / smoke: `python -m pip install -e .`, `PYTHONPATH=. pytest -q`.
- Static checks: `ruff check .`, `black --check .`, `mypy .`.
- Verifiers: `python tools/verifiers/Verify-Atlas.py`, `Verify-PatchNotes.py`, `Verify-Brains.py`,
  `Verify-Handoff.py`, `PYTHONPATH=. python tools/verifiers/Verify-UI-Contract.py`.
- Manual QA: upload CSVs using `PhotonEnergy (keV)` or `Axis (PHz)` columns and confirm overlay plots render
  in the expected wavelength range with the new axis summary captions reflecting the detection method.
