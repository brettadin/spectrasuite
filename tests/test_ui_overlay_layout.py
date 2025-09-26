from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from streamlit.testing.v1 import AppTest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.state.session import AppSessionState, XAxisUnit
from server.models import CanonicalSpectrum, TraceMetadata


def _session_with_traces(count: int) -> AppSessionState:
    session = AppSessionState()
    base_wavelength = np.linspace(500.0, 600.0, 25)
    for idx in range(count):
        flux = np.linspace(0.0, 1.0, base_wavelength.size) + idx
        spectrum = CanonicalSpectrum(
            label=f"Trace {idx}",
            wavelength_vac_nm=base_wavelength,
            values=flux,
            value_mode="flux_density",
            value_unit="arb",
            metadata=TraceMetadata(flux_units="arb"),
            provenance=[],
            source_hash=str(idx),
        )
        session.register_trace(spectrum)
    return session


def _render_overlay(session) -> None:
    from app.state.session import XAxisUnit
    from app.ui.overlay import LineOverlaySettings, render_overlay_tab

    class _EmptyCatalog:
        def lines_for_species(self, species: str):
            return []

    settings = LineOverlaySettings(
        species=None,
        mode="relative",
        gamma=1.0,
        threshold=0.0,
        velocity_kms=0.0,
    )
    render_overlay_tab(
        session,
        axis_unit=XAxisUnit.NM,
        catalog=_EmptyCatalog(),
        line_settings=settings,
    )


def test_overlay_plot_remains_visible_with_trace_manager() -> None:
    session = _session_with_traces(12)
    app = AppTest.from_function(_render_overlay, args=(session,)).run()

    charts = app.get("plotly_chart")
    assert charts, "Expected overlay plot to render before interacting with controls"

    expander = app.expander[0]
    assert expander.label == "Trace Manager"
    assert len(expander.checkbox) == len(session.trace_order)

    expected_keys = {f"visible_{trace_id}" for trace_id in session.trace_order}
    observed_keys = {widget.key for widget in expander.checkbox}
    assert observed_keys == expected_keys

    first_key = f"visible_{session.trace_order[0]}"
    expander.checkbox(key=first_key).uncheck().run()
    assert session.trace_views[session.trace_order[0]].is_visible is False

    charts_after = app.get("plotly_chart")
    assert charts_after, "Plot should remain visible after toggling trace visibility"

    metrics_widget = app.multiselect(key="similarity_metrics")
    assert metrics_widget.value == ["cosine", "rmse"]
