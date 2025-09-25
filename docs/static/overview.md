# Spectra App Documentation

Spectra App provides a reproducible environment for ingesting spectra, comparing archival data,
and exporting manifests that replay the current view. The current build includes:

- Overlay, Differential, Star Hub, and Docs tabs within the Streamlit interface.
- ASCII **and FITS** ingestion with canonical wavelength conversion, provenance logging, and
  duplicate detection.
- Export bundles (manifest v2, per-trace CSVs, optional PNG) with a replay stub that
  reconstructs visible traces.
- Fe I line overlays with scaling controls plus an offline SIMBAD resolver fixture, now paired with
  MAST and SDSS archive wiring so resolved targets can pull spectra straight into the overlay.
- Frequency- and energy-based uploads (Hz–PHz, eV/keV/MeV) auto-convert to the wavelength baseline
  during ingest, with provenance capturing the detected axis family.
- Overlay trace manager surfaces the detected axis family, units, detection method, and downstream
  transforms (unit conversions, air↔vacuum shifts, differential operations) to speed up debugging of
  messy uploads and derived products.

Upcoming documentation work will expand this section with end-to-end usage guidance, data-source
citation details, legal notices, and troubleshooting tips.
