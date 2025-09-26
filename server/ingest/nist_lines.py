"""Convert NIST ASD line results into canonical spectra."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Iterable, cast

import numpy as np

from server.models import CanonicalSpectrum, ProvenanceEvent, TraceMetadata, ValueMode


def _prepare_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        wavelength = row.get("wavelength_nm")
        intensity = row.get("relative_intensity")
        if wavelength is None or intensity is None:
            continue
        try:
            numeric_wavelength = float(wavelength)
            numeric_intensity = float(intensity)
        except Exception:
            continue
        prepared.append({**row, "wavelength_nm": numeric_wavelength, "relative_intensity": numeric_intensity})
    prepared.sort(key=lambda item: item["wavelength_nm"])
    return prepared


def _event_timestamp(metadata: dict[str, Any]) -> datetime:
    raw = metadata.get("fetched_at") or metadata.get("cached_at")
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            pass
    return datetime.now(UTC)


def _label(species: str, window: tuple[float, float] | None) -> str:
    if window is None:
        return f"NIST lines: {species}"
    low, high = window
    return f"NIST lines: {species} {low:.1f}–{high:.1f} nm"


def _compute_hash(rows: list[dict[str, Any]], species: str, window: tuple[float, float] | None) -> str:
    payload = {
        "species": species,
        "window": window,
        "rows": rows,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return digest


def to_canonical(
    rows: Iterable[dict[str, Any]],
    metadata: dict[str, Any],
    *,
    app_version: str,
) -> CanonicalSpectrum:
    """Convert raw NIST rows and metadata into a :class:`CanonicalSpectrum`."""

    species = str(metadata.get("species") or "Unknown species")
    window_raw = metadata.get("wavelength_window_nm")
    window: tuple[float, float] | None = None
    if isinstance(window_raw, (list, tuple)) and len(window_raw) == 2:
        try:
            window = (float(window_raw[0]), float(window_raw[1]))
        except Exception:
            window = None

    prepared = _prepare_rows(rows)
    if not prepared:
        raise ValueError("No valid NIST lines were provided")

    wavelengths = np.array([row["wavelength_nm"] for row in prepared], dtype=float)
    intensities = np.array([row["relative_intensity"] for row in prepared], dtype=float)
    preferred = bool(metadata.get("use_ritz_wavelength", True))

    label = _label(species, window)
    trace_metadata = TraceMetadata(
        provider="NIST ASD",
        title=label,
        target=species,
        flux_units=None,
        extra={
            "nist": {
                "species": species,
                "wavelength_window_nm": window,
                "use_ritz_wavelength": preferred,
                "cache_hit": bool(metadata.get("cache_hit", False)),
                "offline_fallback": bool(metadata.get("offline_fallback", False)),
                "fetched_at": metadata.get("fetched_at"),
                "cached_at": metadata.get("cached_at"),
                "source": metadata.get("source"),
                "query": metadata.get("query"),
                "catalog": metadata.get("catalog"),
                "row_count": len(prepared),
                "rows": prepared,
            }
        },
    )

    provenance = [
        ProvenanceEvent(
            step="fetch_nist_lines",
            parameters={
                "species": species,
                "wavelength_window_nm": window,
                "use_ritz_wavelength": preferred,
                "cache_hit": bool(metadata.get("cache_hit", False)),
                "offline_fallback": bool(metadata.get("offline_fallback", False)),
                "row_count": len(prepared),
                "fetched_at": metadata.get("fetched_at"),
                "cached_at": metadata.get("cached_at"),
                "source": metadata.get("source"),
                "query": metadata.get("query"),
                "catalog": metadata.get("catalog"),
                "app_version": app_version,
            },
            timestamp=_event_timestamp(metadata),
        )
    ]

    source_hash = _compute_hash(prepared, species, window)

    return CanonicalSpectrum(
        label=label,
        wavelength_vac_nm=wavelengths,
        values=intensities,
        value_mode=cast(ValueMode, "relative_intensity"),
        value_unit=None,
        metadata=trace_metadata,
        provenance=provenance,
        source_hash=source_hash,
        uncertainties=None,
    )


__all__ = ["to_canonical"]
