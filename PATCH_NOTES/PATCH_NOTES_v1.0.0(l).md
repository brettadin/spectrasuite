# Spectra App v1.0.0 (l) — Archive fetchers come online

## Highlights
- Implemented working archive adapters for MAST and SDSS so Star Hub can surface real spectroscopic products instead of placeholders.
- Added offline regression coverage for the new fetchers, exercising wavelength/range normalisation, metadata capture, and download link assembly without network access.
- Documented the fetcher pipeline in the atlas and bumped version metadata to `1.0.0l` / `1.0.0.dev12`.

## Changes
- Replaced the stubbed MAST adapter with an `astroquery`-backed search that filters spectroscopic observations, normalises wavelength coverage to nanometres, and captures provenance plus direct download URIs.
- Delivered SDSS helpers that resolve spectra by SpecObjID or plate/MJD/fibre, derive wavelength coverage/resolution from FITS tables, and expose canonical flux units and portal/download links.
- Added targeted pytest coverage for both adapters using synthetic `astroquery` stubs and extended the atlas fetcher overview with the new data flow.

## Known Issues
- Fetchers currently return metadata and download URLs; live ingestion into the overlay tab will be wired up in a follow-up once the UI plumbing is prepared.
- Network access remains optional; integration environments without `astroquery` will still need stubs or cached results to exercise full paths.
- Replay tooling and richer documentation continue to track as open items from earlier runs.

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
