# ASCII Ingestion Pipeline

- Parser: `load_ascii_spectrum` uses pandas with `sep=None` autodetection plus header/unit sniffing.
- Header canonicalisation: column labels are normalised into lowercase slugs (camelCase → snake_case,
  punctuation/diacritics stripped) before alias matching to catch `FluxDensity`, `Wave Length`, etc.
- Column aliases: wavelength synonyms (`wavelength`, `lambda`, `nm`, `angstrom`), flux synonyms
  (`flux`, `intensity`, `counts`, `fluxdensity`), optional uncertainty column.
- Units: header text inside parentheses/brackets parsed; defaults to nanometers when ambiguous.
- Air/vac detection: regex search for "air" or "vacuum" in column name/unit; flagged in provenance.
- Metadata scraping: alias map covers (`target`, `target_name`, `object`, `instrument_name`, etc.) with
  null-like strings filtered; promoted into `TraceMetadata.target`/`instrument`/`telescope`.
- Hash: SHA-256 of raw bytes stored for dedup ledger.
- Provenance: `ingest_ascii` event includes filename, columns used, units, air flag, and content hash.
