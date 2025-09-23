"""Spectral unit conversions and intensity family helpers."""

from __future__ import annotations

from typing import Literal

import numpy as np

WavelengthUnit = Literal["nm", "angstrom", "micron", "wavenumber"]
IntensityMode = Literal[
    "flux_density",
    "transmission",
    "absorbance",
    "optical_depth",
    "relative_intensity",
]

_C = 299_792.458  # km / s


def nm_to_angstrom(wavelength_nm: np.ndarray | float) -> np.ndarray:
    return np.asarray(wavelength_nm, dtype=float) * 10.0


def angstrom_to_nm(wavelength_angstrom: np.ndarray | float) -> np.ndarray:
    return np.asarray(wavelength_angstrom, dtype=float) / 10.0


def nm_to_micron(wavelength_nm: np.ndarray | float) -> np.ndarray:
    return np.asarray(wavelength_nm, dtype=float) / 1000.0


def micron_to_nm(wavelength_micron: np.ndarray | float) -> np.ndarray:
    return np.asarray(wavelength_micron, dtype=float) * 1000.0


def nm_to_wavenumber(wavelength_nm: np.ndarray | float) -> np.ndarray:
    return 1e7 / np.asarray(wavelength_nm, dtype=float)


def wavenumber_to_nm(wavenumber: np.ndarray | float) -> np.ndarray:
    return 1e7 / np.asarray(wavenumber, dtype=float)


def convert_axis_from_nm(values_nm: np.ndarray, to_unit: WavelengthUnit) -> np.ndarray:
    if to_unit == "nm":
        return np.asarray(values_nm, dtype=float)
    if to_unit == "angstrom":
        return nm_to_angstrom(values_nm)
    if to_unit == "micron":
        return nm_to_micron(values_nm)
    if to_unit == "wavenumber":
        return nm_to_wavenumber(values_nm)
    raise ValueError(f"Unsupported unit: {to_unit}")


def convert_axis_to_nm(values: np.ndarray, from_unit: WavelengthUnit) -> np.ndarray:
    if from_unit == "nm":
        return np.asarray(values, dtype=float)
    if from_unit == "angstrom":
        return angstrom_to_nm(values)
    if from_unit == "micron":
        return micron_to_nm(values)
    if from_unit == "wavenumber":
        return wavenumber_to_nm(values)
    raise ValueError(f"Unsupported unit: {from_unit}")


def refractive_index_edlen(wavelength_nm: np.ndarray | float) -> np.ndarray:
    """Refractive index of standard air using the Edlén 1966 parameterization."""

    wavelength_um = np.asarray(wavelength_nm, dtype=float) / 1000.0
    sigma2 = (1.0 / wavelength_um) ** 2
    term = 8342.13 + (2406030.0 / (130.0 - sigma2)) + (15997.0 / (38.9 - sigma2))
    return 1.0 + term * 1e-8


def air_to_vacuum(wavelength_air_nm: np.ndarray | float) -> np.ndarray:
    n = refractive_index_edlen(wavelength_air_nm)
    return np.asarray(wavelength_air_nm, dtype=float) * n


def vacuum_to_air(wavelength_vacuum_nm: np.ndarray | float) -> np.ndarray:
    n = refractive_index_edlen(wavelength_vacuum_nm)
    return np.asarray(wavelength_vacuum_nm, dtype=float) / n


def transmission_to_absorbance(transmission: np.ndarray | float) -> np.ndarray:
    transmission_arr = np.clip(np.asarray(transmission, dtype=float), 1e-12, 1.0)
    return -np.log10(transmission_arr)


def absorbance_to_transmission(absorbance: np.ndarray | float) -> np.ndarray:
    absorbance_arr = np.asarray(absorbance, dtype=float)
    return np.power(10.0, -absorbance_arr)


def transmission_to_optical_depth(transmission: np.ndarray | float) -> np.ndarray:
    transmission_arr = np.clip(np.asarray(transmission, dtype=float), 1e-12, 1.0)
    return -np.log(transmission_arr)


def optical_depth_to_transmission(optical_depth: np.ndarray | float) -> np.ndarray:
    optical_depth_arr = np.asarray(optical_depth, dtype=float)
    return np.exp(-optical_depth_arr)


def absorbance_to_optical_depth(absorbance: np.ndarray | float) -> np.ndarray:
    return transmission_to_optical_depth(absorbance_to_transmission(absorbance))


def optical_depth_to_absorbance(optical_depth: np.ndarray | float) -> np.ndarray:
    return transmission_to_absorbance(optical_depth_to_transmission(optical_depth))


def doppler_shift_wavelength(wavelength_nm: np.ndarray, velocity_kms: float) -> np.ndarray:
    factor = 1.0 + velocity_kms / _C
    return np.asarray(wavelength_nm, dtype=float) * factor


__all__ = [
    "IntensityMode",
    "WavelengthUnit",
    "air_to_vacuum",
    "absorbance_to_optical_depth",
    "absorbance_to_transmission",
    "convert_axis_from_nm",
    "convert_axis_to_nm",
    "doppler_shift_wavelength",
    "nm_to_angstrom",
    "nm_to_micron",
    "nm_to_wavenumber",
    "optical_depth_to_absorbance",
    "optical_depth_to_transmission",
    "refractive_index_edlen",
    "transmission_to_absorbance",
    "transmission_to_optical_depth",
    "vacuum_to_air",
    "wavenumber_to_nm",
]
