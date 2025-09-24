# ASCII Ingestion Pipeline

- Parser: `load_ascii_spectrum` still relies on pandas with `sep=None` autodetection but reruns the import
  without headers when the first row looks numeric, preventing leading data from being swallowed as column
  labels.
- Header canonicalisation: column labels are normalised into lowercase slugs (camelCase → snake_case,
  punctuation/diacritics stripped, BOM/zero-width characters removed) so `FluxDensity`, `Wave Length`, or
  BOM-prefixed headers normalise consistently.
- Column detection: explicit wavelength/flux/uncertainty aliases are matched token-wise (so
  `Flux_Total`/`fluxDensity`/`noise` resolve) before we fall back to unit hints (µm/Å/cm⁻¹ for wavelength,
  erg/Jy/photons/arb for flux) and finally numeric heuristics (monotonic ramp ≈ wavelength, remaining
  numeric column ≈ flux) so bare or oddly labelled exports still ingest.
- Error channels: uncertainty-like headers (`*_error`, `*_sigma`, `noise`, etc.) are detected first and
  excluded from wavelength/flux selection so detection no longer latches onto `Flux_Error`/`Wavelength_Error`
  when the primary columns trail them in the file.
- Units: header text inside parentheses/brackets is parsed and canonicalised (µm → `um`, Å → `angstrom`);
  when numeric heuristics select the columns we still surface `unknown` to avoid leaking placeholder
  headers like `column_0`.
- Row filtering: rows without finite wavelength/flux pairs are dropped after coercion; provenance logs the
  total/retained counts so downstream tooling understands the trim.
- Air/vac detection: regex search for "air" or "vacuum" in column name/unit; flagged in provenance.
- Metadata scraping: alias map covers (`target`, `target_name`, `object`, `instrument_name`, etc.) with
  null-like strings filtered; promoted into `TraceMetadata.target`/`instrument`/`telescope`.
- Hash: SHA-256 of raw bytes stored for dedup ledger.
- Provenance: `ingest_ascii` records whether detection relied on `aliases`, `unit_hint`, or
  `numeric_heuristic`, whether the upload was headerless, how many rows were retained, plus filename,
  columns, units, the air flag, and content hash.
