from __future__ import annotations

from streamlit.testing.v1 import AppTest

from app.state.session import AppSessionState
from app.ui import main as main_ui
class _FakeCatalog:
    def species(self) -> list[str]:
        return ["Fe I", "Mg II"]


def _render_sidebar_app(session, catalog, settings) -> None:
    from app.ui import main as module_main

    module_main._configure_sidebar(  # type: ignore[attr-defined]
        session,
        catalog,
        settings,
        app_version="9.9.9",
    )


def test_sidebar_form_registers_nist_trace(monkeypatch) -> None:
    session = AppSessionState()
    catalog = _FakeCatalog()

    rows = [
        {
            "wavelength_nm": 500.0,
            "relative_intensity": 100.0,
            "ritz_wavelength_nm": 500.0,
            "transition": "a - b",
        }
    ]
    metadata = {
        "species": "Fe I",
        "wavelength_window_nm": (500.0, 501.0),
        "use_ritz_wavelength": True,
        "cache_hit": False,
        "fetched_at": "2024-01-01T00:00:00+00:00",
        "source": "test",
    }

    def fake_fetch(species, wmin, wmax, *, use_ritz_wavelength, **kwargs):
        assert species == "Fe I"
        assert wmin == 500.0
        assert wmax == 501.0
        assert use_ritz_wavelength is True
        return rows, metadata

    monkeypatch.setattr(main_ui, "fetch_lines", fake_fetch)

    settings = {"line_overlays": {"default_species": "Fe I", "default_window_nm": [500.0, 501.0]}}

    at = AppTest.from_function(
        _render_sidebar_app, args=(session, catalog, settings)
    ).run()
    at.sidebar.button(key="nist_fetch_submit").click().run()

    assert session.trace_order
    trace = session.traces[session.trace_order[-1]]
    assert trace.label.startswith("NIST lines: Fe I")
    assert trace.metadata.extra["nist"]["source"] == "test"
    assert trace.provenance[0].parameters["app_version"] == "9.9.9"
    assert at.sidebar.success[0].value.startswith("Added NIST lines for Fe I")
