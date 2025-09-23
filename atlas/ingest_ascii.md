# ASCII Ingestion Pipeline

- Parser: `load_ascii_spectrum` still relies on pandas with `sep=None` autodetection but now reruns the
  import without headers when the first row looks numeric, preventing leading data from being swallowed as
  column labels.
- Header canonicalisation: column labels are normalised into lowercase slugs (camelCase → snake_case,
  punctuation/diacritics stripped) before alias matching to catch `FluxDensity`, `Wave Length`, etc.
- Column detection: we still prefer explicit wavelength/flux aliases yet fall back to numeric heuristics
  (monotonic ramp ≈ wavelength, remaining numeric column ≈ flux) so bare two-column exports are ingested
  without renaming.
- Units: header text inside parentheses/brackets parsed; when we guessed the columns, wavelength units are
  reported as `unknown` to avoid leaking placeholder headers like `column_0`.
- Row filtering: rows without finite wavelength/flux pairs are dropped after coercion; provenance logs the
  total/retained counts so downstream tooling understands the trim.
- Air/vac detection: regex search for "air" or "vacuum" in column name/unit; flagged in provenance.
- Metadata scraping: alias map covers (`target`, `target_name`, `object`, `instrument_name`, etc.) with
  null-like strings filtered; promoted into `TraceMetadata.target`/`instrument`/`telescope`.
- Hash: SHA-256 of raw bytes stored for dedup ledger.
- Provenance: `ingest_ascii` now records the detection strategy (`aliases` vs `numeric_heuristic`), whether
  the upload was headerless, how many rows were retained, plus filename, columns, units, the air flag, and
  content hash.
