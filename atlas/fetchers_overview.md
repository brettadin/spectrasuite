# Fetchers Overview

- Resolver: `server/fetchers/resolver_simbad.resolve` uses astroquery when available; falls back to
  bundled `simbad_m31.json` fixture for offline tests.
- Product model: `server/fetchers/models.py` defines `Product` and `ResolverResult` dataclasses.
- MAST/SDSS adapters currently stubbed (raise `NotImplementedError`), documenting future expansion
  path without breaking import graph.
- Tests rely on fixture path; network lookups optional.
