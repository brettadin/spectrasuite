"""Robust ASCII spectrum ingestion with header sniffing."""

from __future__ import annotations

import hashlib
import io
import re
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from server.models import ProvenanceEvent, TraceMetadata

_WAVE_ALIASES = {
    "wavelength",
    "wavelength_nm",
    "wavelength_air",
    "lambda",
    "lambda_nm",
    "wl",
    "wave",
    "nm",
    "angstrom",
}

_FLUX_ALIASES = {
    "flux",
    "flux_density",
    "intensity",
    "counts",
    "flux_erg",
    "flux_jy",
}

_UNCERTAINTY_ALIASES = {"uncertainty", "error", "sigma", "err", "flux_error"}
_METADATA_COLUMNS = {"target", "object", "instrument", "telescope", "observer"}
_UNIT_PATTERN = re.compile(r"(?P<name>[^()\[]+)(?:\s*[\[(](?P<unit>[^)\]]+)[)\]])?", re.IGNORECASE)
_STANDARD_PATTERN = re.compile(r"(vacuum|air)", re.IGNORECASE)


@dataclass(slots=True)
class ASCIIIngestResult:
    label: str
    wavelength: np.ndarray
    wavelength_unit: str
    flux: np.ndarray
    flux_unit: str | None
    uncertainties: np.ndarray | None
    metadata: TraceMetadata
    provenance: list[ProvenanceEvent]
    is_air_wavelength: bool
    content_hash: str


class ASCIIIngestError(RuntimeError):
    pass


def _normalise_header(column: str) -> tuple[str, str | None]:
    match = _UNIT_PATTERN.match(column.strip())
    if not match:
        return column.strip().lower(), None
    name = match.group("name").strip().lower()
    unit_raw = match.group("unit")
    unit = unit_raw.strip().lower() if unit_raw else None
    return name, unit


def _detect_column(columns: Iterable[str], aliases: set[str]) -> str | None:
    for column in columns:
        normalised, _ = _normalise_header(column)
        if normalised in aliases:
            return column
    return None


def _detect_standard(column: str, unit_hint: str | None) -> bool:
    """Return True if the column name/unit hints at air wavelengths."""

    column_lc = column.lower()
    if _STANDARD_PATTERN.search(column_lc):
        return "air" in column_lc
    if unit_hint and _STANDARD_PATTERN.search(unit_hint.lower()):
        return "air" in unit_hint.lower()
    return False


def _infer_label(df: pd.DataFrame, filename: str) -> str:
    for candidate in ("target", "object", "name"):
        if candidate in df.columns and df[candidate].notna().any():
            value = str(df[candidate].iloc[0]).strip()
            if value:
                return value
    stem = filename.rsplit("/", 1)[-1]
    return stem.split(".")[0]


def load_ascii_spectrum(file_bytes: bytes, filename: str) -> ASCIIIngestResult:
    """Load an ASCII spectrum and return the parsed arrays plus metadata."""

    if not file_bytes:
        raise ASCIIIngestError("Empty file provided")

    content_hash = hashlib.sha256(file_bytes).hexdigest()
    text = file_bytes.decode("utf-8", errors="replace")
    buffer = io.StringIO(text)

    try:
        df = pd.read_csv(buffer, comment="#", sep=None, engine="python").dropna(how="all")
    except Exception as exc:  # pragma: no cover - surfaced in tests
        raise ASCIIIngestError(f"Failed to parse ASCII spectrum: {exc}") from exc

    if df.empty:
        raise ASCIIIngestError("No rows detected in spectrum file")

    wave_column = _detect_column(df.columns, _WAVE_ALIASES)
    if wave_column is None:
        raise ASCIIIngestError("No wavelength column detected")

    flux_column = _detect_column(df.columns, _FLUX_ALIASES)
    if flux_column is None:
        raise ASCIIIngestError("No flux/intensity column detected")

    uncertainty_column = _detect_column(df.columns, _UNCERTAINTY_ALIASES)

    wave_name, wave_unit = _normalise_header(wave_column)
    flux_name, flux_unit = _normalise_header(flux_column)
    is_air = _detect_standard(wave_column, wave_unit)

    wavelength = np.asarray(df[wave_column], dtype=float)
    flux = np.asarray(df[flux_column], dtype=float)
    uncertainties = None
    if uncertainty_column is not None:
        uncertainties = np.asarray(df[uncertainty_column], dtype=float)

    metadata = TraceMetadata()
    for column in _METADATA_COLUMNS:
        if column in df.columns:
            value = df[column].iloc[0]
            if isinstance(value, str):
                value = value.strip()
            metadata.extra[column] = value
    metadata.target = metadata.extra.get("target") or metadata.extra.get("object")
    metadata.instrument = metadata.extra.get("instrument")
    metadata.telescope = metadata.extra.get("telescope")

    provenance = [
        ProvenanceEvent(
            step="ingest_ascii",
            parameters={
                "filename": filename,
                "wave_column": wave_column,
                "flux_column": flux_column,
                "uncertainty_column": uncertainty_column,
                "wave_unit": wave_unit or "unknown",
                "flux_unit": flux_unit or "unknown",
                "is_air": is_air,
                "hash": content_hash,
            },
        )
    ]

    label = _infer_label(df, filename)

    return ASCIIIngestResult(
        label=label,
        wavelength=wavelength,
        wavelength_unit=wave_unit or wave_name,
        flux=flux,
        flux_unit=flux_unit,
        uncertainties=uncertainties,
        metadata=metadata,
        provenance=provenance,
        is_air_wavelength=is_air,
        content_hash=content_hash,
    )


__all__ = ["ASCIIIngestError", "ASCIIIngestResult", "load_ascii_spectrum"]
