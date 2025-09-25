# Spectra App v1.0.0 (m) — Star Hub ingestion

## Highlights
- Wired the Star Hub tab to run SIMBAD resolves into live MAST searches and SDSS fetchers so archive
  spectra can be added to overlays with a single click.
- Added an archive product ingestion utility that downloads FITS/ASCII payloads, merges catalog
  metadata into the canonical trace, and records provenance for reproducibility.
- Updated documentation to reflect the new archive workflow and bumped version metadata to
  `1.0.0m` / `1.0.0.dev13`.

## Changes
- Implemented `server.fetchers.ingest_product.ingest_product` with download helpers, metadata merging,
  and provenance logging plus regression coverage.
- Rebuilt the Star Hub UI around resolver state, MAST searches, and SDSS selectors with direct
  "Add to overlay" controls.
- Documented the ingest pathway in `atlas/fetchers_overview.md` and refreshed the docs overview to
  mention archive wiring.

## Known Issues
- Archive downloads still rely on network access; offline workflows should supply cached payloads or
  mock fetchers.
- Citation/DOI coverage remains limited to what the archives expose; richer attribution will follow
  once mission-specific metadata is catalogued.
- Replay tooling and expanded docs remain open items from earlier runs.

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

