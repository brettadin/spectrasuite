# Spectra App v1.0.0 (p) — Provider federation

## Highlights
- Introduced a provider registry with deduplicated fan-out across MAST, SDSS, ESO, and DOI adapters.
- Refreshed Star Hub to resolve once, persist filters, surface previews, and ingest multiple products in one action.
- Added regression coverage for provider registration, ESO/DOI adapters, and the Streamlit flow that pulls selected spectra into overlays.

## Changes
- Added `server/providers/__init__.py` defining `ProviderQuery`, `ProviderHit`, registry helpers, and `search_all(...)` orchestration.
- Updated MAST and SDSS adapters to emit `ProviderHit` records and wired new ESO/DOI sample adapters into the registry.
- Reworked `server/fetchers/resolver_simbad.resolve` with an explicit fixture toggle and rewrote `app/ui/star_hub.py` around the provider registry and multi-select ingestion.
- Documented the provider federation in `atlas/fetchers_overview.md` and refreshed the Star Hub summary in `docs/static/overview.md`.

## Known Issues
- ESO/DOI adapters ship curated samples rather than live archive queries; future runs can replace them with production clients.
- Preview rendering relies on remote URLs; offline runs fall back to simple preview links when images cannot be fetched.
- Registry fan-out currently swallows provider exceptions silently; we may want structured error reporting in a follow-up.

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
