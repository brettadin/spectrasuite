from __future__ import annotations

from server.ingest.ascii_loader import load_ascii_spectrum
from server.ingest.canonicalize import canonicalize_ascii, normalise_wavelength_unit


def test_air_to_vacuum_provenance() -> None:
    content = b"Wavelength_air (angstrom),Flux\n" b"5000,1.0\n" b"5001,1.1\n"
    ascii_result = load_ascii_spectrum(content, "air_example.csv")
    canonical = canonicalize_ascii(ascii_result)
    steps = [event.step for event in canonical.provenance]
    assert "air_to_vacuum" in steps
    assert canonical.metadata.wavelength_standard == "vacuum"


def test_normalise_wavelength_unit_extended_energy() -> None:
    assert normalise_wavelength_unit("keV") == "energy_kev"
    assert normalise_wavelength_unit("MeV") == "energy_mev"
    assert normalise_wavelength_unit("PHz") == "frequency_phz"
