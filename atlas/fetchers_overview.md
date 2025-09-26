# Fetchers Overview

- Resolver: `server/fetchers/resolver_simbad.resolve` uses astroquery when available and supports an
  explicit `use_fixture=True` toggle to fall back to the bundled `simbad_m31.json` payload for
  offline tests.
- Product model: `server/fetchers/models.py` defines `Product` and `ResolverResult` dataclasses used
  across archive adapters.
- Providers: `server/providers/__init__.py` implements the shared `ProviderQuery`/`ProviderHit`
  models, a registry, and `search_all(...)` fan-out with duplicate suppression across provider hits.
- MAST: `server/fetchers/mast.search_products` queries the archive via `astroquery.mast.Observations`
  when available, filtering for spectroscopic products and emitting `ProviderHit` records with
  normalised wavelength bounds, provenance hints, and portal/download links. Offline tests
  monkeypatch the client to avoid network access while exercising the canonicalisation path.
- SDSS: `server/fetchers/sdss.search_spectra` runs region queries through `astroquery.sdss.SDSS`,
  derives coverage/resolution from FITS tables, and emits `ProviderHit` metadata alongside the
  direct spectrum download link. `fetch_by_specobjid`/`fetch_by_plate` remain available for targeted
  lookups.
- ESO: `server/fetchers/eso.search` provides curated VLT sample spectra for offline demos,
  honouring instrument/telescope filters while populating preview/download metadata.
- DOI: `server/fetchers/doi.search` resolves curated DOI mappings to archive products so DOI lookups
  surface in the provider grid with deduplication against the originating archive.
- Ingest: `server.fetchers.ingest_product.ingest_product` downloads archive payloads (FITS preferred,
  ASCII fallback) and runs them through the canonical ingest pipeline. Metadata from `Product`
  models merges into `TraceMetadata`, provenance logs the fetch step, and duplicates are avoided via
  the existing session ledger.
- Star Hub fans out a resolved target to the provider registry, persists provider/telescope/
  instrument/λ filters in `st.session_state`, renders previews where available, and supports
  multi-select overlay ingestion.
- Tests rely on local fixtures/stubs; network lookups remain optional for integration runs.
