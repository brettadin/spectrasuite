from __future__ import annotations

from pathlib import Path

from app.ui.overlay import (
    _collect_transform_notes,
    _extract_axis_summary,
    _format_axis_caption,
)
from server.ingest.ascii_loader import load_ascii_spectrum
from server.ingest.canonicalize import canonicalize_ascii, canonicalize_fits
from server.ingest.fits_loader import load_fits_spectrum
from server.math.differential import subtract
from server.models import ProvenanceEvent


def test_axis_summary_for_ascii_trace() -> None:
    fixture = Path("data/examples/example_spectrum.csv")
    result = load_ascii_spectrum(fixture.read_bytes(), fixture.name)
    canonical = canonicalize_ascii(result)

    summary = _extract_axis_summary(canonical)
    assert summary is not None
    assert summary.axis_family == "wavelength"
    assert summary.detection_method == "aliases"

    caption = _format_axis_caption(summary)
    assert "Axis family: `wavelength`" in caption
    assert "via aliases" in caption


def test_axis_summary_for_headerless_ascii() -> None:
    content = b"5100,1.23\n5110,1.19\n5120,1.17\n"
    result = load_ascii_spectrum(content, "headerless.csv")
    canonical = canonicalize_ascii(result)

    summary = _extract_axis_summary(canonical)
    assert summary is not None
    assert summary.axis_family == "unknown"
    assert summary.detection_method == "numeric_heuristic"
    assert summary.headerless

    caption = _format_axis_caption(summary)
    assert "headerless heuristic" in caption


def test_axis_summary_for_fits_trace() -> None:
    fixture = Path("data/examples/example_spectrum.fits")
    result = load_fits_spectrum(fixture)
    canonical = canonicalize_fits(result)

    summary = _extract_axis_summary(canonical)
    assert summary is not None
    assert summary.axis_family == "wavelength"
    assert summary.detection_method == "fits"

    caption = _format_axis_caption(summary)
    assert "via fits" in caption


def test_transform_notes_include_axis_conversions() -> None:
    content = b"Wavelength_air (angstrom),Flux\n5100,1.0\n5110,0.9\n"
    result = load_ascii_spectrum(content, "air_units.csv")
    canonical = canonicalize_ascii(result)

    notes = _collect_transform_notes(canonical)
    assert any(note.startswith("Axis converted") for note in notes)
    assert any("Air→vacuum" in note for note in notes)


def test_transform_notes_include_differential_events() -> None:
    fixture = Path("data/examples/example_spectrum.csv")
    base_result = load_ascii_spectrum(fixture.read_bytes(), fixture.name)
    base = canonicalize_ascii(base_result)
    offset_content = b"Wavelength (nm),Flux (arb),target\n500.0,0.9,Example Star\n500.5,1.0,Example Star\n501.0,0.8,Example Star\n501.5,0.95,Example Star\n502.0,1.1,Example Star\n"
    offset_result = load_ascii_spectrum(offset_content, "offset.csv")
    other = canonicalize_ascii(offset_result)

    product = subtract(base, other)
    assert product is not None
    product.spectrum.provenance.append(
        ProvenanceEvent(step="differential_ui_add", parameters={"operation": product.operation})
    )

    notes = _collect_transform_notes(product.spectrum)
    assert any(note.startswith("Differential subtract") for note in notes)
    assert any("Added via differential tab" in note for note in notes)
