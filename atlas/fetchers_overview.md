# Fetchers Overview

- Resolver: `server/fetchers/resolver_simbad.resolve` uses astroquery when available; falls back to
  bundled `simbad_m31.json` fixture for offline tests.
- Product model: `server/fetchers/models.py` defines `Product` and `ResolverResult` dataclasses.
- MAST: `server/fetchers/mast.search_products` queries the archive via `astroquery.mast.Observations`
  when available, filtering for spectroscopic products and augmenting metadata with direct download
  URIs from the product list. The adapter normalises wavelength bounds to nanometres, extracts
  pipeline provenance, and records auxiliary fields (collection, filters, exposure) in the `extra`
  payload. Offline tests monkeypatch the client to avoid network access while exercising the
  canonicalisation path.
- SDSS: `server/fetchers/sdss.fetch_by_specobjid` / `fetch_by_plate` resolve metadata through
  `astroquery.sdss.SDSS.query_specobj`, pull the calibrated spectrum via `get_spectra`, and derive
  wavelength coverage/resolution from the FITS table. Products advertise vacuum wavelengths,
  standard SDSS flux units (`1e-17 erg s^-1 cm^-2 Å^-1`), and include canonical download/portal
  links. Offline coverage patches the SDSS client with synthetic tables/HDU lists.
- Ingest: `server.fetchers.ingest_product.ingest_product` downloads archive payloads (FITS preferred,
  ASCII fallback) and runs them through the canonical ingest pipeline. Metadata from the `Product`
  model is merged into the resulting `TraceMetadata`, provenance logs the fetch step, and duplicates
  are avoided via the existing session ledger.
- Star Hub surfaces resolver output alongside MAST search results and SDSS fetch helpers so analysts
  can add archive spectra directly to the overlay without leaving the app.
- Tests rely on local fixtures/stubs; network lookups remain optional for integration runs.
