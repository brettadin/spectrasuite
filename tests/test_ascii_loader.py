from __future__ import annotations

from pathlib import Path

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
    content = "\ufeffWavelength (nm),Flux (arb),Target\n510.0,1.2,Example Object\n".encode("utf-8")
    result = load_ascii_spectrum(content, "bom.csv")
    assert result.wavelength_unit == "nm"
    assert result.metadata.target == "Example Object"
    canonical = canonicalize_ascii(result)
    assert canonical.metadata.target == "Example Object"


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
