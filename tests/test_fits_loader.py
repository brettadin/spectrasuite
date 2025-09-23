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


def test_load_fits_spectrum_supports_companion_wavelength_table(tmp_path: Path) -> None:
    wavelengths = np.array([4100.0, 4200.0, 4300.0, 4400.0], dtype=float)
    flux = np.array([1.2, 0.9, 1.8, 1.1], dtype=float)
    inverse_variance = np.array([25.0, 16.0, 9.0, 4.0], dtype=float)

    flux_hdu = fits.BinTableHDU.from_columns(
        [
            fits.Column(
                name="FLUX",
                format="D",
                array=flux,
                unit="erg / (Angstrom cm2 s)",
            ),
            fits.Column(name="IVAR", format="D", array=inverse_variance),
        ],
        name="SPECTRUM",
    )
    flux_hdu.header["OBJECT"] = "SDSS Target"
    flux_hdu.header["INSTRUME"] = "BOSS"
    flux_hdu.header["AIRORVAC"] = "vac"

    wave_hdu = fits.BinTableHDU.from_columns(
        [fits.Column(name="LOGLAM", format="D", array=np.log10(wavelengths))],
        name="WAVE",
    )

    path = tmp_path / "sdss_like.fits"
    fits.HDUList([fits.PrimaryHDU(), flux_hdu, wave_hdu]).writeto(path)

    result = load_fits_spectrum(path)

    assert result.metadata.instrument == "BOSS"
    assert result.wavelength_unit.lower() == "angstrom"
    assert np.allclose(result.wavelength, wavelengths)

    expected_sigma = np.full(inverse_variance.shape, np.nan, dtype=float)
    mask = inverse_variance > 0
    expected_sigma[mask] = 1.0 / np.sqrt(inverse_variance[mask])
    assert result.uncertainties is not None
    assert np.allclose(result.uncertainties, expected_sigma, equal_nan=True)

    provenance = result.provenance[0].parameters["wcs"]
    assert provenance["source"] == "companion_column"
    assert provenance["column"].lower() == "loglam"


def test_load_fits_spectrum_uses_specutils_fallback(tmp_path: Path) -> None:
    wavelengths = np.array([5100.0, 5125.0, 5155.0], dtype=float)
    flux = np.array([0.5, 0.7, 0.6], dtype=float)
    sigma = np.array([0.05, 0.07, 0.06], dtype=float)

    table_hdu = fits.BinTableHDU.from_columns(
        [
            fits.Column(name="FLUX", format="D", array=flux, unit="erg / (Angstrom cm2 s)"),
            fits.Column(name="AXIS", format="D", array=wavelengths, unit="Angstrom"),
            fits.Column(name="SIGMA", format="D", array=sigma, unit="erg / (Angstrom cm2 s)"),
        ],
        name="DATA",
    )
    table_hdu.header["OBJECT"] = "Specutils Source"
    table_hdu.header["INSTRUME"] = "FallbackSpec"
    table_hdu.header["AIRORVAC"] = "vac"

    path = tmp_path / "specutils_table.fits"
    fits.HDUList([fits.PrimaryHDU(), table_hdu]).writeto(path)

    result = load_fits_spectrum(path)

    assert result.metadata.instrument == "FallbackSpec"
    assert np.allclose(result.wavelength, wavelengths)
    assert result.wavelength_unit.lower() == "angstrom"
    assert result.uncertainties is not None
    assert np.allclose(result.uncertainties, sigma)

    provenance = result.provenance[0].parameters["wcs"]
    assert provenance["source"] == "specutils"
    assert provenance["format"] in {"auto", "tabular-fits"}
