from __future__ import annotations

from pathlib import Path

import numpy as np

from app.state.session import AppSessionState
from server.ingest.ascii_loader import load_ascii_spectrum
from server.ingest.canonicalize import canonicalize_ascii


def test_ascii_loader_parses_units(tmp_path: Path) -> None:
    fixture = Path("data/examples/example_spectrum.csv")
    content = fixture.read_bytes()
    result = load_ascii_spectrum(content, fixture.name)
    assert result.wavelength_unit == "nm"
    assert result.metadata.target == "Example Star"
    canonical = canonicalize_ascii(result)
    assert canonical.metadata.flux_units == "arb"


def test_ascii_loader_handles_bom_headers() -> None:
    content = "\ufeffWavelength (nm),Flux (arb),Target\n510.0,1.2,Example Object\n".encode()


    content = "\ufeffWavelength (nm),Flux (arb),Target\n510.0,1.2,Example Object\n".encode()

    content = "\ufeffWavelength (nm),Flux (arb),Target\n510.0,1.2,Example Object\n".encode("utf-8")

    result = load_ascii_spectrum(content, "bom.csv")
    assert result.wavelength_unit == "nm"
    assert result.metadata.target == "Example Object"
    canonical = canonicalize_ascii(result)
    assert canonical.metadata.target == "Example Object"



def test_ascii_loader_handles_messy_synonyms() -> None:
    content = b"\n".join(
        [
            b"Wave Length [Angstrom],FluxDensity,OBJECT NAME,Instrument Name,Telescope-name,Observer",
            b"5100,1.23e-16,Messy Target,Messy Instrument,Messy Telescope,Astronomer",
            b"",
        ]
    )
    result = load_ascii_spectrum(content, "messy.csv")
    assert result.wavelength_unit == "angstrom"
    assert result.label == "Messy Target"
    assert result.metadata.target == "Messy Target"
    assert result.metadata.instrument == "Messy Instrument"
    assert result.metadata.telescope == "Messy Telescope"
    assert result.metadata.extra["observer"] == "Astronomer"
    canonical = canonicalize_ascii(result)
    assert canonical.metadata.target == "Messy Target"
    assert canonical.metadata.instrument == "Messy Instrument"



def test_session_deduplication() -> None:
    fixture = Path("data/examples/example_spectrum.csv")
    result = load_ascii_spectrum(fixture.read_bytes(), fixture.name)
    canonical = canonicalize_ascii(result)
    session = AppSessionState()
    added, trace_id = session.register_trace(canonical)
    assert added
    added_again, duplicate_id = session.register_trace(canonical)
    assert not added_again
    assert duplicate_id == trace_id


def test_ascii_loader_guesses_numeric_columns() -> None:
    content = b"5100,1.23\n5110,1.19\n5120,1.17\n"
    result = load_ascii_spectrum(content, "headerless.csv")
    np.testing.assert_allclose(result.wavelength, np.array([5100.0, 5110.0, 5120.0]))
    np.testing.assert_allclose(result.flux, np.array([1.23, 1.19, 1.17]))
    assert result.wavelength_unit == "unknown"
    assert result.label == "headerless"
    params = result.provenance[0].parameters
    assert params["detection_method"] == "numeric_heuristic"
    assert params["headerless"]
    assert params["rows_retained"] == 3


def test_ascii_loader_uses_unit_hints_for_detection() -> None:
    content = b"\n".join(
        [
            b"Channel (\xc2\xb5m),Band (erg/s/cm^2/A),Noise (erg/s/cm^2/A)",
            b"0.95,1.2,0.1",
            b"1.05,1.1,0.2",
            b"",
        ]
    )
    result = load_ascii_spectrum(content, "unit_hints.csv")
    np.testing.assert_allclose(result.wavelength, np.array([0.95, 1.05]))
    np.testing.assert_allclose(result.flux, np.array([1.2, 1.1]))
    assert result.wavelength_unit in {"µm", "μm"}
    assert result.flux_unit == "erg/s/cm^2/a"
    params = result.provenance[0].parameters
    assert params["detection_method"] == "unit_hint"
    assert params["wave_column"] == "Channel (µm)"
    assert params["flux_column"] == "Band (erg/s/cm^2/A)"


def test_ascii_loader_handles_wavenumber_units() -> None:
    content = b"\n".join(
        [
            b"SpatialFreq (cm^-1),Signal (photons/s),RMS (photons/s)",
            b"1000,5.0,0.1",
            b"1010,4.5,0.2",
            b"",
        ]
    )
    result = load_ascii_spectrum(content, "wavenumber.csv")
    np.testing.assert_allclose(result.wavelength, np.array([1000.0, 1010.0]))
    np.testing.assert_allclose(result.flux, np.array([5.0, 4.5]))
    assert result.wavelength_unit == "cm^-1"
    assert result.flux_unit == "photons/s"
    params = result.provenance[0].parameters
    assert params["detection_method"] == "unit_hint"
    assert params["wave_column"] == "SpatialFreq (cm^-1)"
    assert params["flux_column"] == "Signal (photons/s)"


def test_ascii_loader_ignores_error_prefixed_columns() -> None:
    content = b"\n".join(
        [
            b"Wavelength_Error (nm),Wavelength (nm),Flux_Error,Flux,Note",
            b"0.1,5100,0.05,1.2,first",
            b"0.2,5110,0.04,1.1,second",
            b"0.3,5120,0.03,1.05,third",
            b"",
        ]
    )
    result = load_ascii_spectrum(content, "errors_first.csv")
    np.testing.assert_allclose(result.wavelength, np.array([5100.0, 5110.0, 5120.0]))
    np.testing.assert_allclose(result.flux, np.array([1.2, 1.1, 1.05]))
    assert result.uncertainties is not None
    np.testing.assert_allclose(result.uncertainties, np.array([0.05, 0.04, 0.03]))
    params = result.provenance[0].parameters
    assert params["detection_method"] == "aliases"
    assert params["wave_column"] == "Wavelength (nm)"
    assert params["flux_column"] == "Flux"
    assert params["uncertainty_column"] == "Flux_Error"
