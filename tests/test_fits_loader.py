from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

from server.ingest.canonicalize import canonicalize_fits
from server.ingest.fits_loader import load_fits_spectrum


def test_load_fits_spectrum_extracts_metadata() -> None:
    fixture = Path("data/examples/example_spectrum.fits")
    result = load_fits_spectrum(fixture)

    assert result.label == "Example FITS Star"
    assert result.metadata.instrument == "MockSpec"
    assert result.flux_unit == "erg/s/cm2/A"
    assert result.uncertainties is not None
    assert result.uncertainties.shape == result.flux.shape

    canonical = canonicalize_fits(result)
    assert canonical.metadata.wavelength_standard == "vacuum"
    assert np.isclose(canonical.wavelength_vac_nm[0], 500.0)
    assert canonical.metadata.wave_range_nm is not None


def test_canonicalize_fits_converts_air_wavelengths(tmp_path: Path) -> None:
    flux = np.ones(4, dtype=float)
    header = fits.Header()
    header["CRVAL1"] = 6000.0
    header["CDELT1"] = 2.0
    header["CRPIX1"] = 1.0
    header["CTYPE1"] = "AWAV"
    header["CUNIT1"] = "angstrom"
    header["OBJECT"] = "Air Source"

    path = tmp_path / "air_spectrum.fits"
    fits.HDUList([fits.PrimaryHDU(data=flux, header=header)]).writeto(path)

    result = load_fits_spectrum(path)
    assert result.is_air_wavelength

    canonical = canonicalize_fits(result)
    assert canonical.metadata.wavelength_standard == "vacuum"
    assert canonical.wavelength_vac_nm[0] > 600.0
    assert "air_to_vacuum" in {event.step for event in canonical.provenance}
