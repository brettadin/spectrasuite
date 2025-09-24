from __future__ import annotations

from pathlib import Path

from app.ui.overlay import _extract_axis_summary, _format_axis_caption
from server.ingest.ascii_loader import load_ascii_spectrum
from server.ingest.canonicalize import canonicalize_ascii, canonicalize_fits
from server.ingest.fits_loader import load_fits_spectrum


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
