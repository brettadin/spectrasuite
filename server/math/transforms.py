"""Spectral unit conversions and intensity family helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import numpy as np

WavelengthUnit = Literal[
    "nm",
    "angstrom",
    "micron",
    "wavenumber",
    "frequency_hz",
    "frequency_khz",
    "frequency_mhz",
    "frequency_ghz",
    "frequency_thz",
    "energy_ev",
]
IntensityMode = Literal[
    "flux_density",
    "transmission",
    "absorbance",
    "optical_depth",
    "relative_intensity",
]

_C = 299_792.458  # km / s
_C_M_PER_S = 299_792_458.0
_HC_EV_NM = 1239.8419843320026


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


def frequency_to_nm(frequency: np.ndarray | float, *, scale: float = 1.0) -> np.ndarray:
    frequency_hz = np.asarray(frequency, dtype=float) * scale
    with np.errstate(divide="ignore", invalid="ignore"):
        wavelength_nm = np.divide(
            _C_M_PER_S * 1e9,
            frequency_hz,
            out=np.full_like(frequency_hz, np.inf, dtype=float),
            where=frequency_hz != 0.0,
        )
    return wavelength_nm


def nm_to_frequency(wavelength_nm: np.ndarray | float, *, scale: float = 1.0) -> np.ndarray:
    wavelength_m = np.asarray(wavelength_nm, dtype=float) * 1e-9
    with np.errstate(divide="ignore", invalid="ignore"):
        frequency_hz = np.divide(
            _C_M_PER_S,
            wavelength_m,
            out=np.full_like(wavelength_m, np.inf, dtype=float),
            where=wavelength_m != 0.0,
        )
    return frequency_hz / scale


def energy_ev_to_nm(energy_ev: np.ndarray | float) -> np.ndarray:
    energy = np.asarray(energy_ev, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        wavelength_nm = np.divide(
            _HC_EV_NM,
            energy,
            out=np.full_like(energy, np.inf, dtype=float),
            where=energy != 0.0,
        )
    return wavelength_nm


def nm_to_energy_ev(wavelength_nm: np.ndarray | float) -> np.ndarray:
    wavelength = np.asarray(wavelength_nm, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        energy_ev = np.divide(
            _HC_EV_NM,
            wavelength,
            out=np.full_like(wavelength, np.inf, dtype=float),
            where=wavelength != 0.0,
        )
    return energy_ev


_CONVERT_FROM_NM: dict[WavelengthUnit, Callable[[np.ndarray], np.ndarray]] = {
    "nm": lambda values: np.asarray(values, dtype=float),
    "angstrom": nm_to_angstrom,
    "micron": nm_to_micron,
    "wavenumber": nm_to_wavenumber,
    "frequency_hz": lambda values: nm_to_frequency(values, scale=1.0),
    "frequency_khz": lambda values: nm_to_frequency(values, scale=1e3),
    "frequency_mhz": lambda values: nm_to_frequency(values, scale=1e6),
    "frequency_ghz": lambda values: nm_to_frequency(values, scale=1e9),
    "frequency_thz": lambda values: nm_to_frequency(values, scale=1e12),
    "energy_ev": nm_to_energy_ev,
}

_CONVERT_TO_NM: dict[WavelengthUnit, Callable[[np.ndarray], np.ndarray]] = {
    "nm": lambda values: np.asarray(values, dtype=float),
    "angstrom": angstrom_to_nm,
    "micron": micron_to_nm,
    "wavenumber": wavenumber_to_nm,
    "frequency_hz": lambda values: frequency_to_nm(values, scale=1.0),
    "frequency_khz": lambda values: frequency_to_nm(values, scale=1e3),
    "frequency_mhz": lambda values: frequency_to_nm(values, scale=1e6),
    "frequency_ghz": lambda values: frequency_to_nm(values, scale=1e9),
    "frequency_thz": lambda values: frequency_to_nm(values, scale=1e12),
    "energy_ev": energy_ev_to_nm,
}


def convert_axis_from_nm(values_nm: np.ndarray, to_unit: WavelengthUnit) -> np.ndarray:
    try:
        converter = _CONVERT_FROM_NM[to_unit]
    except KeyError as exc:
        raise ValueError(f"Unsupported unit: {to_unit}") from exc
    return converter(values_nm)


def convert_axis_to_nm(values: np.ndarray, from_unit: WavelengthUnit) -> np.ndarray:
    try:
        converter = _CONVERT_TO_NM[from_unit]
    except KeyError as exc:
        raise ValueError(f"Unsupported unit: {from_unit}") from exc
    return converter(values)


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
    "energy_ev_to_nm",
    "frequency_to_nm",
    "doppler_shift_wavelength",
    "nm_to_angstrom",
    "nm_to_micron",
    "nm_to_wavenumber",
    "nm_to_energy_ev",
    "nm_to_frequency",
    "optical_depth_to_absorbance",
    "optical_depth_to_transmission",
    "refractive_index_edlen",
    "transmission_to_absorbance",
    "transmission_to_optical_depth",
    "vacuum_to_air",
    "wavenumber_to_nm",
]
