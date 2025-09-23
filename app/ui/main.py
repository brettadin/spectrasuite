"""Main Streamlit entry point."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st
import yaml

from app.state.session import AppSessionState, DisplayMode, XAxisUnit, get_session_state
from app.ui.differential import render_differential_tab
from app.ui.docs import render_docs_tab
from app.ui.overlay import LineOverlaySettings, OverlayRenderResult, render_overlay_tab
from app.ui.star_hub import render_star_hub_tab
from server.export.manifest import export_session
from server.fetchers import resolver_simbad  # noqa: F401 - ensure module discovery
from server.overlays.lines import LineCatalog


@dataclass(slots=True)
class UIContract:
    tabs: list[str]
    sidebar_sections: list[str]
    version_badge_label: str


@dataclass(slots=True)
class AppConfig:
    app_version: str
    schema_version: int
    settings: dict[str, Any]


def load_config() -> AppConfig:
    root = Path(__file__).resolve().parents[2]
    version_payload = json.loads((root / "app" / "config" / "version.json").read_text())
    settings_payload = yaml.safe_load((root / "app" / "config" / "settings.yaml").read_text())
    return AppConfig(
        app_version=version_payload["app_version"],
        schema_version=int(version_payload["schema_version"]),
        settings=settings_payload,
    )


def get_ui_contract() -> UIContract:
    return UIContract(
        tabs=["Overlay", "Differential", "Star Hub", "Docs"],
        sidebar_sections=[
            "Examples",
            "Display Mode",
            "Units",
            "Duplicate Scope",
            "Line Overlays",
        ],
        version_badge_label="Version",
    )


def _configure_sidebar(
    session: AppSessionState, catalog: LineCatalog, settings: dict[str, Any]
) -> LineOverlaySettings:
    st.sidebar.header("Examples")
    st.sidebar.write("Load bundled examples from data/examples in future runs.")

    st.sidebar.header("Display Mode")
    display_choice = st.sidebar.radio(
        "Y-axis mode",
        options=[DisplayMode.FLUX_DENSITY.value, DisplayMode.RELATIVE_INTENSITY.value],
        index=0 if session.display_mode == DisplayMode.FLUX_DENSITY else 1,
        key="display_mode_radio",
    )
    session.set_display_mode(DisplayMode(display_choice))

    st.sidebar.header("Units")
    axis_unit = st.sidebar.radio(
        "Wavelength units",
        options=[unit.value for unit in XAxisUnit],
        index=list(XAxisUnit).index(session.x_axis_unit),
        key="axis_unit_radio",
    )
    session.set_axis_unit(XAxisUnit(axis_unit))

    st.sidebar.header("Duplicate Scope")
    session.duplicate_scope = st.sidebar.selectbox(
        "Duplicate policy",
        options=["session", "global"],
        index=0,
        key="duplicate_scope_select",
    )

    st.sidebar.header("Line Overlays")
    species_options = catalog.species()
    default_species = settings.get("line_overlays", {}).get("default_species")
    species_index = (
        species_options.index(default_species) if default_species in species_options else 0
    )
    species = st.sidebar.selectbox("Species", species_options, index=species_index)
    mode = st.sidebar.selectbox("Scaling mode", ["relative", "quantile"])
    gamma = st.sidebar.slider("Gamma", min_value=0.6, max_value=1.0, value=0.85, step=0.05)
    threshold = st.sidebar.slider(
        "Relative threshold", min_value=0.0, max_value=1.0, value=0.0, step=0.05
    )
    velocity = st.sidebar.slider(
        "Δv (km/s)", min_value=-300.0, max_value=300.0, value=0.0, step=5.0
    )

    return LineOverlaySettings(
        species=species, mode=mode, gamma=gamma, threshold=threshold, velocity_kms=velocity
    )


def _header(app_version: str) -> None:
    st.title("Spectra App")
    st.caption("Research-grade spectral comparison toolkit")
    st.markdown(f"**Version:** `{app_version}`")
    st.text_input("Global search", placeholder="Search traces or metadata", key="global_search")


def run_app() -> None:
    config = load_config()
    st.set_page_config(page_title="Spectra App", layout="wide")
    session = get_session_state(st, default=AppSessionState())
    catalog = LineCatalog()

    _header(config.app_version)

    line_settings = _configure_sidebar(session, catalog, config.settings)

    overlay_tab, differential_tab, star_hub_tab, docs_tab = st.tabs(get_ui_contract().tabs)

    export_result: OverlayRenderResult | None = None
    with overlay_tab:
        export_result = render_overlay_tab(
            session,
            axis_unit=session.x_axis_unit,
            catalog=catalog,
            line_settings=line_settings,
        )
    with differential_tab:
        render_differential_tab(session)
    with star_hub_tab:
        render_star_hub_tab(session)
    with docs_tab:
        render_docs_tab()

    figure = export_result.figure if export_result else None
    overlay_settings = export_result.overlay_settings if export_result else {}

    if st.button("Export current view", key="export_button"):
        bundle = export_session(
            session,
            figure,
            app_version=config.app_version,
            schema_version=config.schema_version,
            axis_unit=session.x_axis_unit,
            display_mode=session.display_mode.value,
            overlay_settings=overlay_settings,
            include_png=config.settings.get("export", {}).get("include_png", True),
        )
        st.session_state["export_bytes"] = bundle.zip_bytes
        st.success("Export bundle ready. Use the download button below.")

    if "export_bytes" in st.session_state:
        st.download_button(
            "Download export bundle",
            data=st.session_state["export_bytes"],
            file_name="spectra_export.zip",
            mime="application/zip",
        )

    st.status("Ready", expanded=False)


__all__ = ["UIContract", "get_ui_contract", "run_app"]
