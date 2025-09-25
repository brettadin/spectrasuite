# Spectra App v1.0.0 (k) — Transform provenance in the UI

## Highlights
- Extend the Overlay trace manager to summarise downstream provenance, including unit conversions,
  air→vacuum corrections, and differential operations alongside the existing axis family badges.
- Provide immediate visibility into how each trace was transformed after ingest so analysts can audit
  derived spectra without exporting manifests.

## Changes
- Added transform-note extraction in the Overlay UI so axis captions now list unit conversions,
  air-to-vacuum methods, and differential steps recorded in provenance events.
- Expanded regression coverage verifying transform notes for air-wavelength uploads and differential
  products so future changes keep the UI audit trail accurate.
- Updated documentation, atlas UI contract, brains log, handoff, and version metadata to advertise
  `1.0.0k` / `1.0.0.dev11` with the new provenance summaries.

## Known Issues
- Archive fetchers (MAST/SDSS) remain stubbed; Star Hub still relies on fixtures.
- Replay CLI/UI reconstruction tooling and richer docs content remain outstanding.
- Provenance summaries cover ingestion, conversions, and differentials; future runs may extend them to
  other transforms (e.g., resolution matching) as those events are recorded.

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
