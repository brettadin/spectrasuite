# Spectra App

Spectra App is a research-grade Streamlit application for comparing uploaded spectra against
archival references with reproducible provenance. This repository follows the "Spectra App —
Fresh Start" master brief and ships with:

- A canonical wavelength baseline (vacuum nanometers) with reversible unit toggles.
- Robust ASCII and FITS ingestion with provenance logging and deduplication.
- Export bundles that reproduce the visible state via a manifest (schema v2).
- Continuity artifacts in `/atlas`, `/brains`, `/PATCH_NOTES`, and `/handoffs` to keep every
  run auditable.

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
streamlit run app/app_patched.py
```

## Testing & Quality Gates

```bash
ruff check .
black --check .
mypy .
pytest
```

## Documentation

- Atlas: system design notes per subsystem (`/atlas`).
- Brains: run journal (`/brains`).
- Patch notes: user-facing change log (`/PATCH_NOTES`).
- Handoffs: cross-run context (`/handoffs`).

The Docs tab inside the app renders the content from `docs/static/`.
