# HANDOFF 1.0.0i — High-energy axis support

## 1) Summary of This Run
- Added keV/MeV energy support to ASCII ingestion and transforms so high-energy exports canonicalise
  correctly.
- Recognised petahertz frequency units in ingestion, transforms, and canonicalisation for UV/X-ray spectra.
- Surfaced the interpreted axis family in ASCII provenance to improve debugging of unit detection.
- Updated documentation, patch notes, brains log, and metadata to advertise `1.0.0i` / `1.0.0.dev9`.

## 2) Current State of the Project
- **Working tabs:** Overlay, Differential, Star Hub (SIMBAD), Line Atlas, Docs, upload history with
  provenance capturing detection method, retained rows, axis family, and content hash.
- **Data ingestion:** ASCII loader handles wavelength, wavenumber, frequency (Hz→PHz), and energy (eV/keV/MeV)
  axes with uncertainty filtering; FITS loader unchanged.
- **Docs & comms:** Atlas, patch notes, brains, docs overview, and this handoff reflect the new high-energy
  support.

## 3) Next Steps (Prioritized)
1. Surface the axis family within the UI (e.g., provenance sidebar) so humans see the classification quickly.
2. Extend unit hints if future datasets arrive with meV or alternate frequency aliases (e.g., m⁻¹, GHz ranges).
3. Continue archive fetcher build-out so high-energy spectra from MAST/SDSS exercise the new pipeline.

## 4) Decisions & Rationale
- Layered the new conversions on existing transform helpers to avoid duplicating physics constants.
- Reused the alias/unit-hint pipeline for classification so behaviour stays deterministic and covered by
  existing regression tests.
- Defaulted axis family to `wavelength` when no markers appear to keep provenance informative without adding
  noise for well-labelled uploads.

## 5) References
- Atlas: `atlas/ingest_ascii.md`, `atlas/transforms.md`
- Patch notes: `PATCH_NOTES/PATCH_NOTES_v1.0.0(i).md`
- Brains log: `brains/v1.0.0i__assistant__energy_axis_extensions.md`

## 6) Quick Start for the Next AI
- Install deps / smoke: `python -m pip install -e .`, `PYTHONPATH=. pytest -q`.
- Static checks: `ruff check .`, `black --check .`, `mypy .`.
- Verifiers: `python tools/verifiers/Verify-Atlas.py`, `Verify-PatchNotes.py`, `Verify-Brains.py`,
  `Verify-Handoff.py`, `PYTHONPATH=. python tools/verifiers/Verify-UI-Contract.py`.
- Manual QA: upload CSVs using `PhotonEnergy (keV)` or `Axis (PHz)` columns and confirm overlay plots render
  in the expected wavelength range with provenance listing the new axis family.
