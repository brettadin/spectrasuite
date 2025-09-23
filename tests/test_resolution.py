from __future__ import annotations

import numpy as np

from server.math.resolution import estimate_fwhm, match_resolution


def _gaussian(wavelengths: np.ndarray, center: float, sigma: float) -> np.ndarray:
    return np.exp(-0.5 * ((wavelengths - center) / sigma) ** 2)


def test_match_resolution_reduces_resolving_power() -> None:
    wavelengths = np.linspace(500.0, 501.0, 1001)
    flux = _gaussian(wavelengths, 500.5, 0.01)
    result = match_resolution(
        wavelengths, flux, current_resolution=10000.0, target_resolution=2000.0
    )
    fwhm = estimate_fwhm(wavelengths, result.flux)
    expected_fwhm = np.median(wavelengths) / 2000.0
    assert abs(fwhm - expected_fwhm) / expected_fwhm < 0.2
