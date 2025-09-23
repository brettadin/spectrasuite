# ASCII Ingestion Pipeline

- Parser: `load_ascii_spectrum` uses pandas with `sep=None` autodetection plus header/unit sniffing.
- Column aliases: wavelength synonyms (`wavelength`, `lambda`, `nm`, `angstrom`), flux synonyms
  (`flux`, `intensity`, `counts`), optional uncertainty column.
- Units: header text inside parentheses/brackets parsed; defaults to nanometers when ambiguous.
- Air/vac detection: regex search for "air" or "vacuum" in column name/unit; flagged in provenance.
- Metadata scraping: optional columns (`target`, `object`, `instrument`, `telescope`, `observer`)
  recorded into `TraceMetadata.extra` with `target`/`instrument`/`telescope` promoted.
- Hash: SHA-256 of raw bytes stored for dedup ledger.
- Provenance: `ingest_ascii` event includes filename, columns used, units, air flag, and content hash.
