"""Radial-velocity frame corrections."""

from __future__ import annotations

from typing import Literal

import numpy as np

from server.math.transforms import doppler_shift_wavelength

FrameTag = Literal["topocentric", "heliocentric", "barycentric", "unknown", "none"]


_C = 299_792.458  # km/s


def shift_to_rest_frame(wavelength_nm: np.ndarray, velocity_kms: float) -> np.ndarray:
    """Remove a radial velocity from observed wavelengths."""

    factor = 1.0 / (1.0 + velocity_kms / _C)
    return np.asarray(wavelength_nm, dtype=float) * factor


def shift_from_rest_frame(wavelength_nm: np.ndarray, velocity_kms: float) -> np.ndarray:
    """Apply a radial velocity to rest-frame wavelengths."""

    return doppler_shift_wavelength(wavelength_nm, velocity_kms)


__all__ = ["FrameTag", "shift_from_rest_frame", "shift_to_rest_frame"]
