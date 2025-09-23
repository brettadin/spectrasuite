# Canonical Data Model

- Baseline axis: `wavelength_vac_nm` (float64 numpy array) stored on each `CanonicalSpectrum`.
- Value modes supported: `flux_density` initially; differential ratio results produce
  `relative_intensity`.
- Metadata: `TraceMetadata` tracks provider, product id, instrument, telescope, resolving power,
  wavelength standard, flux units, frame, radial velocity, URLs, citation, DOI, and `extra` dict.
- Provenance: `ProvenanceEvent` appended for ingestion, unit conversions, air→vacuum transform,
  and UI-triggered differentials/export.
- Session ledger: dedup signature `(source_hash, product_id or label)` prevents duplicate ingest
  unless overridden by UI (Allow duplicates flag unused yet).
