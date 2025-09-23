"""Overlay tab implementation."""

from __future__ import annotations

import io
from dataclasses import dataclass

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from app.state.session import AppSessionState, XAxisUnit
from server.ingest.ascii_loader import ASCIIIngestError, load_ascii_spectrum
from server.ingest.canonicalize import canonicalize_ascii, canonicalize_fits
from server.ingest.fits_loader import FITSIngestError, load_fits_spectrum
from server.math import transforms
from server.overlays.lines import LineCatalog, apply_velocity_shift, scale_lines


@dataclass(slots=True)
class LineOverlaySettings:
    species: str | None
    mode: str
    gamma: float
    threshold: float
    velocity_kms: float


@dataclass(slots=True)
class OverlayRenderResult:
    figure: go.Figure | None
    overlay_settings: dict


def _plot_lines(
    catalog: LineCatalog,
    axis_unit: XAxisUnit,
    settings: LineOverlaySettings,
) -> tuple[list[float | None], list[float | None]]:
    if settings.species is None:
        return [], []
    try:
        entries = catalog.lines_for_species(settings.species)
    except FileNotFoundError:
        return [], []
    scaled = scale_lines(
        entries, mode=settings.mode, gamma=settings.gamma, min_relative_intensity=settings.threshold
    )
    if settings.velocity_kms != 0:
        scaled = apply_velocity_shift(scaled, settings.velocity_kms)
    x_values: list[float | None] = []
    y_values: list[float | None] = []
    for line in scaled:
        converted = transforms.convert_axis_from_nm(
            np.array([line.wavelength_nm]), axis_unit.value
        )[0]
        x_values.extend([converted, converted, None])
        y_values.extend([0.0, line.display_height, None])
    return x_values, y_values


def _render_trace_controls(session: AppSessionState) -> None:
    st.subheader("Trace Manager")
    for trace_id in session.trace_order:
        trace = session.traces[trace_id]
        view = session.trace_views[trace_id]
        checkbox = st.checkbox(
            f"{trace.label}",
            value=view.is_visible,
            key=f"visible_{trace_id}",
            help=f"Flux units: {trace.metadata.flux_units}",
        )
        session.toggle_visibility(trace_id, checkbox)


def _plot_traces(session: AppSessionState, axis_unit: XAxisUnit) -> go.Figure:
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    for trace_id in session.trace_order:
        view = session.trace_views[trace_id]
        if not view.is_visible:
            continue
        trace = session.traces[trace_id]
        axis_values = transforms.convert_axis_from_nm(trace.wavelength_vac_nm, axis_unit.value)
        figure.add_trace(
            go.Scattergl(
                x=axis_values,
                y=trace.values,
                mode="lines",
                name=trace.label,
                hovertemplate="%{x:.3f}, %{y:.3e}",
            ),
            secondary_y=False,
        )
    figure.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title=f"Wavelength ({axis_unit.value})",
        yaxis_title="Flux",
        yaxis2_title="Line strength",
    )
    figure.update_yaxes(showgrid=True)
    return figure


def render_overlay_tab(
    session: AppSessionState,
    *,
    axis_unit: XAxisUnit,
    catalog: LineCatalog,
    line_settings: LineOverlaySettings,
) -> OverlayRenderResult:
    st.subheader("Upload Spectra")
    uploaded_files = st.file_uploader(
        "Upload CSV/TXT/FITS spectra",
        type=["csv", "txt", "dat", "fits", "fit", "fts"],
        accept_multiple_files=True,
        key="overlay_uploader",
    )
    if uploaded_files:
        for uploaded in uploaded_files:
            try:
                name_lower = uploaded.name.lower()
                payload = uploaded.getvalue()
                if name_lower.endswith((".csv", ".txt", ".dat")):
                    raw = load_ascii_spectrum(payload, uploaded.name)
                    canonical = canonicalize_ascii(raw)
                elif name_lower.endswith((".fits", ".fit", ".fts")):
                    result = load_fits_spectrum(io.BytesIO(payload), filename=uploaded.name)
                    canonical = canonicalize_fits(result)
                else:
                    st.warning(f"Unsupported file type for '{uploaded.name}'")
                    continue
                added, trace_id = session.register_trace(canonical)
                if added:
                    st.success(f"Added trace '{canonical.label}'")
                else:
                    st.warning(f"Duplicate detected for '{canonical.label}' (trace {trace_id})")
            except (ASCIIIngestError, FITSIngestError) as err:
                st.error(str(err))

    _render_trace_controls(session)
    figure = _plot_traces(session, axis_unit)

    line_x, line_y = _plot_lines(catalog, axis_unit, line_settings)
    if line_x and figure is not None:
        figure.add_trace(
            go.Scatter(
                x=line_x,
                y=line_y,
                mode="lines",
                name=f"{line_settings.species} lines",
                line=dict(color="#888888", width=1.5),
            ),
            secondary_y=True,
        )

    st.plotly_chart(figure, use_container_width=True, config={"scrollZoom": True})

    st.caption(
        "Wavelength baseline: vacuum nanometers. Unit toggles are idempotent and reversible."
    )

    overlay_payload = {
        "line_overlay": {
            "species": line_settings.species,
            "mode": line_settings.mode,
            "gamma": line_settings.gamma,
            "threshold": line_settings.threshold,
            "velocity_kms": line_settings.velocity_kms,
        }
    }

    return OverlayRenderResult(figure=figure, overlay_settings=overlay_payload)


__all__ = ["LineOverlaySettings", "OverlayRenderResult", "render_overlay_tab"]
