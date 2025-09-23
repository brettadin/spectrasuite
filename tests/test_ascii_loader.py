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
