---
title: "Citations & Data Sources"
group: "References"
order: 0
summary: "Reference links for spectral line catalogs, unit conversions, and archival datasets."
---

# Citations & Data Sources

## Spectral Line References

- **NIST Atomic Spectra Database (ASD)** — Primary source for Fe I line lists and transition metadata used in overlays. <https://physics.nist.gov/asd>
- **Kelly, R. L. (1987)** *Atomic and Ionic Spectrum Lines below 2000 Å.* National Standard Reference Data System. Serves as a secondary validation reference for key transitions.

## Unit Conversion & Spectral Utilities

- **Astropy Collaboration et al. (2022)** — *The Astropy Project: Sustaining and Growing a Community-oriented Open-source Project*. `astropy.units` provides conversions between frequency/energy/wavelength bases. <https://doi.org/10.3847/1538-4365/ac7c74>
- **Specutils Documentation** — Guides for spectrum representations, uncertainty handling, and resampling strategies leveraged in ingestion. <https://specutils.readthedocs.io/en/stable/>

## Archival Data Providers

- **MAST (Barbara A. Mikulski Archive for Space Telescopes)** — JWST, HST, and related mission products. <https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html>
- **SDSS (Sloan Digital Sky Survey)** — Optical spectra and photometry across multiple data releases. <https://www.sdss.org/>
- **ESO Science Archive** — Spectroscopic products from VLT, La Silla, and survey programmes. <https://archive.eso.org/>
- **Zenodo / DOI-backed Repositories** — Community-submitted spectra packaged with persistent identifiers. <https://zenodo.org/>

## Usage & Attribution

- Cite the original archive when publishing analyses derived from retrieved spectra; include dataset DOIs or proposal IDs where available.
- When referencing this application, cite the Spectra App version listed in `app/config/version.json` alongside this documentation bundle.
- Export manifests embed provider metadata and retrieval timestamps to simplify audit trails.
