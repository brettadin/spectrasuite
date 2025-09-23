# Architecture Overview

- Front-end: Streamlit app composed of modular tab renderers (`app/ui/*`).
- State: `AppSessionState` stores traces, visibility flags, and ingest dedupe ledger.
- Server layer: ingestion in `server/ingest`, maths in `server/math`, overlays in `server/overlays`,
  export in `server/export`.
- Shared data model: `server/models.py` defines `CanonicalSpectrum`, `TraceMetadata`, and
  `ProvenanceEvent`.
- Export pipeline: `export_session` bundles manifest, PNG (via Kaleido), and per-trace CSVs.
- Continuity: `/atlas`, `/brains`, `/PATCH_NOTES`, and `/handoffs` updated each run.
