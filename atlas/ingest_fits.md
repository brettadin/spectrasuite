# Ingest — FITS Spectra

## Overview
- `server/ingest/fits_loader.py` parses 1D FITS spectra from either table or image HDUs and
  normalises them into a shared ingest result. The loader is resilient to:
  - Tables with `WAVELENGTH`/`FLUX` columns (including `loglam` grids that are exponentiated).
  - Image HDUs with linear WCS dispersion (`CRVAL1`, `CDELT1`, `CRPIX1`, `CTYPE1`, `CUNIT1`).
  - Companion uncertainty data stored as error columns or dedicated `ERR`-style HDUs.
- Provenance captures the selected HDU, wavelength/flux units, air/vacuum hints, a SHA-256 hash,
  and WCS keywords used to build the grid.
- Metadata harvested from headers populates `TraceMetadata` (target, instrument, telescope, RA/Dec,
  resolving power, pipeline version, spectral frame, observer, exposure time).

## Canonicalisation
- `canonicalize_fits` (in `server/ingest/canonicalize.py`) mirrors the ASCII flow: convert the
  wavelength axis to vacuum nanometres, log the transform, and perform air→vacuum conversion when
  `AWAV`/`AIRORVAC` indicates air wavelengths.
- The resulting `CanonicalSpectrum` retains uploaded flux units, uncertainties, and provenance.
- `metadata.wave_range_nm` is populated from the converted dispersion for quick coverage badges.

## UI Integration
- The Overlay tab uploader now accepts `.fits/.fit/.fts` files. Uploaded FITS payloads feed
  through the new loader and canonicaliser before entering session state with deduplication logic.
- Example FITS data: `data/examples/example_spectrum.fits` (linear vacuum wavelength grid with
  matching error HDU) underpins automated tests and manual smoke checks.
