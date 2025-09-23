"""Resolution matching helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import gaussian_filter1d


@dataclass(slots=True)
class ResolutionMatchResult:
    flux: np.ndarray
    kernel_sigma_px: float
    target_resolution: float


def _median_spacing(wavelength_nm: np.ndarray) -> float:
    diffs = np.diff(np.asarray(wavelength_nm, dtype=float))
    diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
    if diffs.size == 0:
        return 0.0
    return float(np.median(diffs))


def match_resolution(
    wavelength_nm: np.ndarray,
    flux: np.ndarray,
    current_resolution: float | None,
    target_resolution: float,
) -> ResolutionMatchResult:
    """Convolve a high-resolution spectrum to the requested resolving power."""

    if target_resolution <= 0:
        raise ValueError("target_resolution must be positive")

    if current_resolution is not None and target_resolution >= current_resolution:
        return ResolutionMatchResult(
            flux=np.asarray(flux, dtype=float),
            kernel_sigma_px=0.0,
            target_resolution=target_resolution,
        )

    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    flux = np.asarray(flux, dtype=float)

    spacing = _median_spacing(wavelength_nm)
    if spacing <= 0:
        return ResolutionMatchResult(
            flux=flux, kernel_sigma_px=0.0, target_resolution=target_resolution
        )

    lam_ref = float(np.median(wavelength_nm))
    current_fwhm = lam_ref / current_resolution if current_resolution else 0.0
    target_fwhm = lam_ref / target_resolution
    kernel_fwhm = np.sqrt(max(target_fwhm**2 - current_fwhm**2, 0.0))
    sigma_nm = kernel_fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    sigma_px = sigma_nm / spacing
    if not np.isfinite(sigma_px) or sigma_px <= 0:
        return ResolutionMatchResult(
            flux=flux, kernel_sigma_px=0.0, target_resolution=target_resolution
        )

    blurred = gaussian_filter1d(flux, sigma=sigma_px, mode="nearest")
    return ResolutionMatchResult(
        flux=blurred, kernel_sigma_px=float(sigma_px), target_resolution=target_resolution
    )


def estimate_fwhm(wavelength_nm: np.ndarray, flux: np.ndarray) -> float:
    """Estimate the FWHM of the central peak for validation."""

    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    flux = np.asarray(flux, dtype=float)
    peak_index = int(np.argmax(flux))
    peak_value = flux[peak_index]
    half_max = peak_value / 2.0
    left_indices = np.where(flux[:peak_index] <= half_max)[0]
    right_indices = np.where(flux[peak_index:] <= half_max)[0]
    if left_indices.size == 0 or right_indices.size == 0:
        return 0.0
    left = wavelength_nm[left_indices[-1]]
    right = wavelength_nm[peak_index + right_indices[0]]
    return float(right - left)


__all__ = ["ResolutionMatchResult", "estimate_fwhm", "match_resolution"]
