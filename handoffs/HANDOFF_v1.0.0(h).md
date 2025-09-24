# HANDOFF 1.0.0h — Frequency & energy ingestion
## 1) Summary of This Run
- Enabled ASCII ingestion to recognise frequency (Hz/THz) and energy (eV) axes so spectra exported
  outside wavelength space map cleanly to the canonical baseline.
- Extended the transforms module with Hz↔nm and eV↔nm conversions and added regression coverage for
  the new unit families.
- Updated atlas/docs, patch notes, brains, and metadata to advertise `1.0.0h` / `1.0.0.dev8`.

## 2) Current State of the Project
- **Working tabs:** Overlay, Differential, Star Hub (SIMBAD), Line Atlas, Docs, upload history with
  provenance capturing detection method, retained rows, and content hash.
- **Data ingestion:** ASCII loader now handles wavelength, wavenumber, frequency, and energy axes with
  uncertainty filtering; FITS loader unchanged.
- **Docs & comms:** Atlas, patch notes, brains journal, docs overview, and this handoff reflect the
  new frequency/energy support.

## 3) Next Steps (Prioritized)
1. Extend energy handling to keV/MeV and additional frequency units once representative exports arrive.
2. Surface the detected unit family (frequency/energy) explicitly in provenance for richer debugging.
3. Continue archive fetcher build-out so frequency-domain products from MAST/SDSS exercise the new path.

## 4) Decisions & Rationale
- Leaned on unit hints for generic headers to keep alias scoring deterministic while still rescuing
  frequency-labelled datasets.
- Limited energy coverage to eV to avoid guessing scale factors; future work can add keV/MeV with
  explicit conversion constants once validated data is available.
- Reused existing provenance schema rather than minting new detection flags to keep compatibility with
  earlier uploads and exports.

## 5) References
- Atlas: `atlas/ingest_ascii.md`, `atlas/transforms.md`
- Patch notes: `PATCH_NOTES/PATCH_NOTES_v1.0.0(h).md`
- Brains log: `brains/v1.0.0h__assistant__frequency_energy_ingest.md`

## 6) Quick Start for the Next AI
- Install deps / smoke: `python -m pip install -e .`, `PYTHONPATH=. pytest -q`.
- Static checks: `ruff check .`, `black --check .`, `mypy .`.
- Verifiers: `python tools/verifiers/Verify-Atlas.py`, `Verify-PatchNotes.py`, `Verify-Brains.py`,
  `Verify-Handoff.py`, `PYTHONPATH=. python tools/verifiers/Verify-UI-Contract.py`.
- Manual QA: upload CSVs using `Axis (THz)` or `PhotonEnergy (eV)` columns and confirm the overlay plots
  render in the expected wavelength range with provenance listing the new units.
