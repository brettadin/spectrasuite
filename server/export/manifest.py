"""Manifest writer and replay utilities."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from app.state.session import AppSessionState, XAxisUnit
from server.math import transforms
from server.models import CanonicalSpectrum


@dataclass(slots=True)
class ExportBundle:
    manifest: dict
    zip_bytes: bytes


def build_manifest(
    session: AppSessionState,
    *,
    app_version: str,
    schema_version: int,
    axis_unit: XAxisUnit,
    display_mode: str,
    overlay_settings: dict | None = None,
) -> dict:
    visible_traces: list[dict] = []
    for trace_id in session.trace_order:
        view = session.trace_views[trace_id]
        if not view.is_visible:
            continue
        trace = session.traces[trace_id]
        visible_traces.append(
            {
                "trace_id": trace_id,
                "label": trace.label,
                "data": trace.to_manifest_entry(),
                "view": {
                    "is_derived": view.is_derived,
                    "is_pinned": view.is_pinned,
                },
            }
        )

    manifest = {
        "schema_version": schema_version,
        "app_version": app_version,
        "created_utc": datetime.now(UTC).isoformat(),
        "axis": {
            "unit": axis_unit.value,
            "baseline": "wavelength_vac_nm",
        },
        "display_mode": display_mode,
        "traces": visible_traces,
        "overlay": overlay_settings or {},
    }
    return manifest


def _write_trace_csv(trace: CanonicalSpectrum, *, axis_unit: XAxisUnit) -> bytes:
    axis_values = transforms.convert_axis_from_nm(trace.wavelength_vac_nm, axis_unit.value)
    buffer = BytesIO()
    header = f"wavelength_{axis_unit.value},value"
    if trace.uncertainties is not None:
        header += ",uncertainty"
    buffer.write((header + "\n").encode("utf-8"))
    for idx, wavelength in enumerate(axis_values):
        value = trace.values[idx]
        if trace.uncertainties is not None:
            line = f"{wavelength:.8e},{value:.8e},{trace.uncertainties[idx]:.8e}\n"
        else:
            line = f"{wavelength:.8e},{value:.8e}\n"
        buffer.write(line.encode("utf-8"))
    return buffer.getvalue()


def export_session(
    session: AppSessionState,
    figure,
    *,
    app_version: str,
    schema_version: int,
    axis_unit: XAxisUnit,
    display_mode: str,
    overlay_settings: dict | None = None,
    include_png: bool = True,
) -> ExportBundle:
    manifest = build_manifest(
        session,
        app_version=app_version,
        schema_version=schema_version,
        axis_unit=axis_unit,
        display_mode=display_mode,
        overlay_settings=overlay_settings,
    )

    buffer = BytesIO()
    with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        if include_png and figure is not None:
            try:
                png_bytes = figure.to_image(format="png")
            except Exception:  # pragma: no cover - depends on kaleido availability
                png_bytes = b""
            archive.writestr("plot.png", png_bytes)
        for trace_id, trace in session.iter_traces():
            view = session.trace_views[trace_id]
            if not view.is_visible:
                continue
            csv_bytes = _write_trace_csv(trace, axis_unit=axis_unit)
            archive.writestr(f"traces/{trace_id}.csv", csv_bytes)

    return ExportBundle(manifest=manifest, zip_bytes=buffer.getvalue())


def replay_manifest(manifest: Mapping[str, object]) -> list[CanonicalSpectrum]:
    raw_traces = manifest.get("traces", [])
    spectra: list[CanonicalSpectrum] = []
    if not isinstance(raw_traces, Sequence):
        return spectra
    for item in raw_traces:
        if not isinstance(item, Mapping):  # pragma: no cover - manifest validation guard
            continue
        data = item.get("data")
        if not isinstance(data, Mapping):
            continue
        spectra.append(CanonicalSpectrum.from_manifest_entry(dict(data)))
    return spectra


__all__ = ["ExportBundle", "build_manifest", "export_session", "replay_manifest"]
