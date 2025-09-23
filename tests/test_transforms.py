from __future__ import annotations

import numpy as np

from server.math import transforms


def test_wavelength_round_trip() -> None:
    values_nm = np.array([100.0, 500.5, 1000.0])
    angstrom = transforms.nm_to_angstrom(values_nm)
    microns = transforms.nm_to_micron(transforms.angstrom_to_nm(angstrom))
    wavenumber = transforms.nm_to_wavenumber(transforms.micron_to_nm(microns))
    result_nm = transforms.wavenumber_to_nm(wavenumber)
    assert np.allclose(values_nm, result_nm)


def test_air_vacuum_round_trip() -> None:
    air = np.array([400.0, 600.0, 900.0])
    vac = transforms.air_to_vacuum(air)
    back_to_air = transforms.vacuum_to_air(vac)
    assert np.allclose(air, back_to_air, rtol=1e-8, atol=1e-8)


def test_intensity_family_round_trip() -> None:
    transmission = np.array([1.0, 0.5, 0.1])
    absorbance = transforms.transmission_to_absorbance(transmission)
    recovered = transforms.absorbance_to_transmission(absorbance)
    assert np.allclose(transmission, recovered)
    optical_depth = transforms.transmission_to_optical_depth(transmission)
    recovered_tau = transforms.optical_depth_to_transmission(optical_depth)
    assert np.allclose(transmission, recovered_tau)
