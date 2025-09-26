from __future__ import annotations

import numpy as np
from streamlit.testing.v1 import AppTest

from app.state.session import AppSessionState, XAxisUnit
from app.ui.overlay import LineOverlaySettings
from server.models import CanonicalSpectrum, TraceMetadata


class _EmptyCatalog:
    def lines_for_species(self, species):
        return []


def _render_overlay_app(session, catalog, settings) -> None:
    from app.state.session import XAxisUnit as _XAxisUnit
    from app.ui.overlay import render_overlay_tab as _render

    _render(session, axis_unit=_XAxisUnit.NM, catalog=catalog, line_settings=settings)


def _make_trace(label: str) -> CanonicalSpectrum:
    wavelengths = np.linspace(500.0, 600.0, 50)
    values = np.linspace(1.0, 2.0, 50)
    metadata = TraceMetadata(flux_units="erg")
    return CanonicalSpectrum(
        label=label,
        wavelength_vac_nm=wavelengths,
        values=values,
        value_mode="flux_density",
        value_unit="erg",
        metadata=metadata,
        provenance=[],
        source_hash=label,
    )


def test_overlay_plot_precedes_trace_manager() -> None:
    session = AppSessionState()
    for idx in range(12):
        trace = _make_trace(f"Trace {idx}")
        added, _ = session.register_trace(trace)
        assert added

    settings = LineOverlaySettings(
        species=None,
        mode="relative",
        gamma=1.0,
        threshold=0.0,
        velocity_kms=0.0,
    )
    catalog = _EmptyCatalog()

    at = AppTest.from_function(_render_overlay_app, args=(session, catalog, settings)).run()

    plots = at.get("plotly_chart")
    assert len(plots) == 1

    trace_manager = at.expander[0]
    assert trace_manager.label == "Trace Manager"
    assert trace_manager.proto.expanded is False

    checkbox_keys = {checkbox.key for checkbox in trace_manager.checkbox}
    assert {f"visible_{trace_id}" for trace_id in session.trace_order}.issubset(checkbox_keys)

    first_trace = session.trace_order[0]
    at = trace_manager.checkbox(key=f"visible_{first_trace}").uncheck().run()

    assert session.trace_views[first_trace].is_visible is False
    assert len(at.get("plotly_chart")) == 1
