# Transforms

- Wavelength conversions: `server/math/transforms.py` implements nm↔Å↔µm↔cm⁻¹ conversions with
  vectorised numpy routines.
- Air/vac: Edlén (1966) refractive index formula; provenance event `air_to_vacuum` records method.
- Intensity family: conversions between transmission, absorbance, optical depth plus epsilon-safe
  bounds.
- Doppler: linear first-order velocity scaling (`doppler_shift_wavelength`).
- Resolution matching: Gaussian kernel computed from desired resolving power using `match_resolution`
  with median wavelength reference; `estimate_fwhm` used in tests.
