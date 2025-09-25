"""Overlay tab implementation."""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from app.state.session import AppSessionState, DisplayMode, XAxisUnit
from server.ingest.ascii_loader import ASCIIIngestError, load_ascii_spectrum
from server.ingest.canonicalize import canonicalize_ascii, canonicalize_fits
from server.ingest.fits_loader import FITSIngestError, load_fits_spectrum
from server.math import transforms
from server.models import CanonicalSpectrum, ProvenanceEvent
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


@dataclass(slots=True)
class AxisSummary:
    axis_family: str
    detection_method: str | None = None
    wave_unit: str | None = None
    wave_column: str | None = None
    headerless: bool = False


_ABSORPTION_MODES: set[str] = {"transmission", "absorbance", "optical_depth"}
_ABSORPTION_UNIT_HINTS: dict[str, str] = {
    "absorb": "absorbance",
    "absorption": "absorbance",
    "transmission": "transmission",
    "transmittance": "transmission",
    "optical_depth": "optical_depth",
    "opticaldepth": "optical_depth",
}


def _format_epsilon(value: object) -> str | None:
    if isinstance(value, int | float):
        return f"{value:g}"
    return None


def _note_from_event(event: ProvenanceEvent) -> str | None:
    params = dict(event.parameters)
    step = event.step
    if step == "convert_wavelength_unit":
        source = str(params.get("from", "unknown"))
        target = str(params.get("to", "nm"))
        return f"Axis converted {source}→{target}"
    if step == "air_to_vacuum":
        method = params.get("method")
        return f"Air→vacuum via {method}" if method else "Air→vacuum conversion"
    if step == "differential_subtract":
        other = params.get("other")
        label = f"Differential subtract vs {other}" if other else "Differential subtract"
        epsilon = _format_epsilon(params.get("epsilon"))
        return f"{label} (ε={epsilon})" if epsilon else label
    if step == "differential_divide":
        other = params.get("other")
        label = f"Differential divide vs {other}" if other else "Differential divide"
        epsilon = _format_epsilon(params.get("epsilon"))
        return f"{label} (ε={epsilon})" if epsilon else label
    if step == "differential_ui_add":
        operation = params.get("operation")
        if isinstance(operation, str) and operation:
            return f"Added via differential tab ({operation})"
        return "Added via differential tab"
    if step == "differential_trivial":
        return "Trivial differential trace"
    return None


def _collect_transform_notes(trace: CanonicalSpectrum) -> list[str]:
    """Describe downstream provenance transforms for a trace."""

    notes: list[str] = []
    for event in trace.provenance:
        note = _note_from_event(event)
        if note:
            notes.append(note)
    return notes


def _extract_axis_summary(trace: CanonicalSpectrum) -> AxisSummary | None:
    for event in trace.provenance:
        if event.step == "ingest_ascii":
            params: dict[str, Any] = dict(event.parameters)
            axis_family = str(params.get("axis_family", "unknown"))
            detection_method = params.get("detection_method")
            wave_unit = params.get("wave_unit")
            wave_column = params.get("wave_column")
            headerless = bool(params.get("headerless", False))
            column_name = str(wave_column) if wave_column is not None else None
            unit = str(wave_unit) if wave_unit is not None else None
            method = str(detection_method) if detection_method is not None else None
            return AxisSummary(
                axis_family=axis_family,
                detection_method=method,
                wave_unit=unit,
                wave_column=column_name,
                headerless=headerless,
            )
        if event.step == "ingest_fits":
            params = dict(event.parameters)
            wave_unit = params.get("wavelength_unit")
            extname = params.get("extname")
            hdu_index = params.get("hdu_index")
            column: str | None = None
            if isinstance(extname, str) and extname.strip():
                column = extname.strip()
            elif hdu_index is not None:
                column = f"HDU {hdu_index}"
            unit = str(wave_unit) if wave_unit is not None else None
            return AxisSummary(
                axis_family="wavelength",
                detection_method="fits",
                wave_unit=unit,
                wave_column=column,
            )
    return None


def _format_axis_caption(summary: AxisSummary) -> str:
    details: list[str] = []
    if summary.wave_unit:
        details.append(f"unit `{summary.wave_unit}`")
    if summary.wave_column:
        details.append(f"column `{summary.wave_column}`")
    if summary.detection_method:
        pretty = summary.detection_method.replace("_", " ")
        details.append(f"via {pretty}")
    if summary.headerless:
        details.append("headerless heuristic")
    if details:
        joined = ", ".join(details)
        return f"Axis family: `{summary.axis_family}` ({joined})"
    return f"Axis family: `{summary.axis_family}`"


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


def _normalise_flux_units(units: str | None) -> str:
    if not units:
        return ""
    compact = units.lower().strip()
    return compact.replace(" ", "_")


def _infer_intensity_mode(trace: CanonicalSpectrum) -> str:
    mode = trace.value_mode
    if mode in _ABSORPTION_MODES:
        return mode

    units = _normalise_flux_units(trace.metadata.flux_units)
    for marker, candidate in _ABSORPTION_UNIT_HINTS.items():
        if marker in units:
            return candidate
    return mode


def _prepare_trace_values(trace: CanonicalSpectrum) -> tuple[np.ndarray, bool]:
    """Prepare Y-values and axis selection for a trace."""

    inferred_mode = _infer_intensity_mode(trace)
    values = np.asarray(trace.values, dtype=float)

    if inferred_mode == "transmission":
        converted = transforms.transmission_to_absorbance(values)
        return converted, True
    if inferred_mode == "optical_depth":
        converted = transforms.optical_depth_to_absorbance(values)
        return converted, True
    if inferred_mode == "absorbance":
        return values, True
    return values, False


def _primary_axis_title(display_mode: DisplayMode) -> str:
    mapping = {
        DisplayMode.FLUX_DENSITY: "Flux density",
        DisplayMode.RELATIVE_INTENSITY: "Relative intensity",
        DisplayMode.TRANSMISSION: "Transmission",
        DisplayMode.ABSORBANCE: "Absorbance",
        DisplayMode.OPTICAL_DEPTH: "Optical depth",
    }
    return mapping.get(display_mode, "Flux")


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
        summary = _extract_axis_summary(trace)
        if summary:
            st.caption(_format_axis_caption(summary))
        transform_notes = _collect_transform_notes(trace)
        if transform_notes:
            st.caption("Transforms: " + "; ".join(transform_notes))


def _plot_traces(
    session: AppSessionState, axis_unit: XAxisUnit, display_mode: DisplayMode
) -> go.Figure:
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    has_absorption = False
    for trace_id in session.trace_order:
        view = session.trace_views[trace_id]
        if not view.is_visible:
            continue
        trace = session.traces[trace_id]
        axis_values = transforms.convert_axis_from_nm(trace.wavelength_vac_nm, axis_unit.value)
        y_values, is_absorption = _prepare_trace_values(trace)
        if is_absorption:
            has_absorption = True
        figure.add_trace(
            go.Scattergl(
                x=axis_values,
                y=y_values,
                mode="lines",
                name=trace.label,
                hovertemplate="%{x:.3f}, %{y:.3e}",
            ),
            secondary_y=is_absorption,
        )
    secondary_title = "Absorbance" if has_absorption else "Line strength"
    figure.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title=f"Wavelength ({axis_unit.value})",
        yaxis_title=_primary_axis_title(display_mode),
        yaxis2_title=secondary_title,
    )
    figure.update_yaxes(showgrid=True)
    if has_absorption:
        figure.update_yaxes(showgrid=True, secondary_y=True)
    else:
        figure.update_yaxes(showgrid=False, secondary_y=True)
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
    figure = _plot_traces(session, axis_unit, session.display_mode)

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


__all__ = [
    "AxisSummary",
    "LineOverlaySettings",
    "OverlayRenderResult",
    "render_overlay_tab",
]
