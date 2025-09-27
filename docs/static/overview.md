---
title: "Project Overview"
group: "Guides"
order: 0
summary: "High-level snapshot of Spectra App features, architecture, and current capabilities."
---

# Spectra App Overview

Spectra App provides a reproducible environment for ingesting spectra, comparing archival data, and
exporting manifests that replay the current view. The platform emphasises provenance, canonical
units, and tooling to cross-check heterogeneous datasets without losing context.

## Feature Highlights

- **Modular interface:** Overlay, Differential, Star Hub, Similarity, and Docs tabs within the
  Streamlit UI.
- **Robust ingestion:** ASCII and FITS (including multi-extension) files auto-detect wavelength and
  flux columns, map them onto a vacuum-wavelength/SI baseline, and annotate provenance.
- **Archive federation:** Star Hub resolves targets once then fans out to provider adapters
  (MAST/SDSS/ESO/DOI) with preview cards and multi-select ingestion into the overlay.
- **Reference tooling:** Fe I line overlays from the NIST Atomic Spectra Database with intensity
  filters and manual scaling aids.
- **Export & replay:** Bundle exporter writes manifest v2 packages containing trace metadata,
  per-trace CSVs, and optional Plotly PNG captures. Replay stubs reconstruct overlays with matching
  provenance metadata.
- **Derived products:** Differential operations, axis conversions (frequency/energy), similarity
  metrics, and transform history logging keep comparisons auditable.

## Architecture Notes

- **State management:** `app/state` centralises session state, while UI tabs under `app/ui` compose
  reusable components.
- **Processing pipelines:** `server/ingest` handles file loading, unit coercion, and metadata
  extraction; `server/analysis` implements derived calculations (differentials, similarity).
- **Reference data:** `atlas/` captures design docs, API contracts, and provider reference
  information to keep future contributions aligned.
- **Documentation:** Markdown under `docs/static/` feeds this tab; additional guides and citations
  surface alongside the overview.

## Roadmap Snapshots

- Archive federation needs richer UI affordances for provider errors and result curation.
- Docs and user-facing guidance are expanding; expect tutorials, citations, and troubleshooting
  notes to grow iteratively.
- Manifest replay automation and interactive annotations are under active investigation.
