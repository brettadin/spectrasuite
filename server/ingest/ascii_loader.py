"""Robust ASCII spectrum ingestion with header sniffing."""

from __future__ import annotations

import hashlib
import io
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, overload

import numpy as np
import pandas as pd

from server.models import ProvenanceEvent, TraceMetadata

_WAVE_ALIASES = (
    "wavelength",
    "wavelength_nm",
    "wavelength_air",
    "wavelength_vac",
    "wavelength_vacuum",
    "wavelengths",
    "wave_length",
    "lambda",
    "lambda_nm",
    "lambda_air",
    "lambda_vac",
    "lambda_vacuum",
    "wl",
    "wave",
    "waves",
    "wavenumbers",
    "wavenumber",
    "wave_number",
    "micron",
    "microns",
    "micrometer",
    "micrometers",
    "micrometre",
    "micrometres",
    "nanometer",
    "nanometers",
    "nanometre",
    "nanometres",
    "um",
    "angstrom",
    "angstroms",
    "channel",
    "channels",
    "pixel",
    "pixels",
)

_FLUX_ALIASES = (
    "flux",
    "flux_density",
    "fluxdensity",
    "flux_total",
    "flux_calibrated",
    "flux_corr",
    "intensity",
    "intensities",
    "signal",
    "signals",
    "counts",
    "count_rate",
    "adu",
    "adu_rate",
    "flux_erg",
    "flux_jy",
    "f_lambda",
    "flambda",
    "fnu",
    "f_nu",
    "reflectance",
    "transmission",
    "transmittance",
    "absorbance",
    "radiance",
    "brightness",
    "response",
    "throughput",
)

_UNCERTAINTY_ALIASES = (
    "uncertainty",
    "uncertainties",
    "error",
    "errors",
    "sigma",
    "sigmas",
    "err",
    "flux_error",
    "flux_err",
    "flux_unc",
    "unc",
    "uncert",
    "std",
    "stddev",
    "stdev",
    "st_dev",
    "variance",
    "var",
    "noise",
    "rms",
)

_AMBIGUOUS_TOKENS = {
    "error",
    "errors",
    "err",
    "unc",
    "uncert",
    "uncertainty",
    "uncertainties",
    "sigma",
    "sigmas",
    "std",
    "stddev",
    "stdev",
    "st_dev",
    "variance",
    "var",
    "noise",
    "rms",
}

_WAVE_PREFERRED_TOKENS = {
    "wave",
    "wavelength",
    "wavelengths",
    "lambda",
    "angstrom",
    "micron",
    "nanometer",
    "nanometre",
    "nanometers",
    "nanometres",
    "um",
    "aa",
    "wavenumber",
    "wavenumbers",
    "channel",
    "channels",
    "pixel",
    "pixels",
}

_FLUX_PREFERRED_TOKENS = {
    "flux",
    "fluxdensity",
    "intensity",
    "intensities",
    "signal",
    "signals",
    "count",
    "counts",
    "adu",
    "adu_rate",
    "radiance",
    "brightness",
    "reflectance",
    "transmission",
    "transmittance",
    "absorbance",
    "throughput",
    "response",
    "photon",
    "photons",
    "band",
    "spectrum",
    "value",
}

_WAVE_UNIT_HINTS = (
    "nm",
    "nanometer",
    "nanometers",
    "nanometre",
    "nanometres",
    "angstrom",
    "angstroms",
    "aa",
    "micron",
    "microns",
    "micrometer",
    "micrometers",
    "micrometre",
    "micrometres",
    "um",
    "wavenumber",
    "cm_1",
    "per_cm",
    "inverse_cm",
)

_FLUX_UNIT_HINTS = (
    "erg",
    "jy",
    "jansky",
    "adu",
    "count",
    "counts",
    "photon",
    "photons",
    "electron",
    "electrons",
    "flux",
    "unitless",
    "relative",
    "arb",
    "arbitrary",
    "w_m_2",
    "watt",
    "power",
    "mag",
    "magnitude",
)
_METADATA_ALIAS_MAP: dict[str, tuple[str, ...]] = {
    "target": ("target", "target_name", "name"),
    "object": ("object", "object_name", "source", "source_name"),
    "instrument": ("instrument", "instrument_name", "spectrograph"),
    "telescope": ("telescope", "telescope_name", "observatory"),
    "observer": ("observer", "observer_name", "pi", "principal_investigator"),
}
_UNIT_PATTERN = re.compile(r"(?P<name>[^()\[]+)(?:\s*[\[(](?P<unit>[^)\]]+)[)\]])?", re.IGNORECASE)
_STANDARD_PATTERN = re.compile(r"(vacuum|air)", re.IGNORECASE)


@dataclass(slots=True)
class _NumericStats:
    column: str
    coverage: float
    monotonic: float
    span: float


@dataclass(slots=True)
class _ColumnInfo:
    original: str
    canonical: str
    tokens: tuple[str, ...]
    unit: str | None
    canonical_unit: str | None
    unit_tokens: tuple[str, ...]


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


def _clean_header(column: str) -> str:
    """Trim whitespace and strip invisible formatting characters."""

    stripped = unicodedata.normalize("NFKC", column).strip()
    if not stripped:
        return stripped
    # Remove zero-width and BOM characters that frequently appear in UTF-8 exports
    cleaned = "".join(ch for ch in stripped if unicodedata.category(ch) != "Cf")
    return cleaned


def _canonicalise_name(name: str) -> str:
    """Collapse a header or unit name into a canonical lookup token."""

    if not name:
        return ""
    normalized = unicodedata.normalize("NFKC", name)
    normalized = (
        normalized.replace("µ", "u")
        .replace("μ", "u")
        .replace("Å", "angstrom")
        .replace("Å", "angstrom")
    )
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    with_separators = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", without_marks)
    tokens = re.sub(r"[^0-9a-zA-Z]+", "_", with_separators.lower())
    canonical = re.sub(r"_+", "_", tokens).strip("_")
    return canonical


def _normalise_header(column: str) -> tuple[str, str | None]:
    cleaned = _clean_header(column)
    match = _UNIT_PATTERN.match(cleaned)
    if not match:
        return _canonicalise_name(cleaned), None
    name = match.group("name").strip()
    unit_raw = match.group("unit")
    unit = unit_raw.strip().lower() if unit_raw else None
    return _canonicalise_name(name), unit


def _tokenize(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(token for token in value.split("_") if token)


def _describe_columns(columns: Iterable[str]) -> list[_ColumnInfo]:
    infos: list[_ColumnInfo] = []
    for column in columns:
        canonical, unit = _normalise_header(column)
        canonical_unit = _canonicalise_name(unit) if unit else None
        infos.append(
            _ColumnInfo(
                original=column,
                canonical=canonical,
                tokens=_tokenize(canonical),
                unit=unit,
                canonical_unit=canonical_unit,
                unit_tokens=_tokenize(canonical_unit),
            )
        )
    return infos


def _alias_match_score(
    info: _ColumnInfo,
    alias_tokens: tuple[str, ...],
    *,
    preferred_tokens: set[str],
    penalty_tokens: set[str],
) -> int | None:
    if not alias_tokens:
        return None
    candidate_tokens = info.tokens or (() if not info.canonical else (info.canonical,))
    if not candidate_tokens:
        return None

    candidate_tuple = tuple(candidate_tokens)
    alias_tuple = tuple(alias_tokens)
    alias_set = set(alias_tuple)
    candidate_set = set(candidate_tuple)

    checks: tuple[tuple[bool, int], ...] = (
        (candidate_tuple == alias_tuple, 100),
        (info.canonical == "_".join(alias_tuple), 95),
        (
            len(candidate_tuple) > len(alias_tuple)
            and candidate_tuple[: len(alias_tuple)] == alias_tuple,
            90,
        ),
        (alias_set == candidate_set, 85),
        (alias_set.issubset(candidate_set), 70),
    )

    base = next((value for matched, value in checks if matched), None)
    if base is None:
        return None

    score = base - len(candidate_tuple)
    if penalty_tokens and candidate_set & penalty_tokens:
        score -= 25
    if preferred_tokens and candidate_set & preferred_tokens:
        score += 10
    return score


def _detect_column(
    infos: Iterable[_ColumnInfo],
    aliases: Iterable[str],
    *,
    exclude: Iterable[str] | None = None,
    preferred_tokens: Iterable[str] | None = None,
    penalty_tokens: Iterable[str] | None = None,
) -> str | None:
    excluded = set(exclude or ())
    preferred = set(preferred_tokens or ())
    penalties = set(penalty_tokens or ())
    best: tuple[int, int, int, str] | None = None
    for alias_index, alias in enumerate(aliases):
        tokens = _tokenize(alias)
        if not tokens:
            continue
        for info_index, info in enumerate(infos):
            if info.original in excluded:
                continue
            score = _alias_match_score(
                info,
                tokens,
                preferred_tokens=preferred,
                penalty_tokens=penalties,
            )
            if score is None:
                continue
            candidate = (score, -alias_index, -info_index, info.original)
            if best is None or candidate > best:
                best = candidate
    if best:
        return best[-1]
    return None


def _detect_by_unit(
    infos: Iterable[_ColumnInfo],
    hints: Iterable[str],
    *,
    exclude: Iterable[str] | None = None,
) -> str | None:
    excluded = set(exclude or ())
    for info in infos:
        if info.original in excluded:
            continue
        if not info.canonical_unit:
            continue
        for hint in hints:
            if not hint:
                continue
            if hint in info.canonical_unit or hint in info.unit_tokens:
                return info.original
    return None


def _apply_unit_hint(
    current: str | None,
    infos: Iterable[_ColumnInfo],
    hints: Iterable[str],
    *,
    exclude: Iterable[str] | None = None,
) -> tuple[str | None, bool]:
    if current is not None:
        return current, False
    candidate = _detect_by_unit(infos, hints, exclude=exclude)
    return candidate, candidate is not None


def _detect_standard(column: str, unit_hint: str | None) -> bool:
    """Return True if the column name/unit hints at air wavelengths."""

    column_lc = _clean_header(column).lower()
    if _STANDARD_PATTERN.search(column_lc):
        return "air" in column_lc
    if unit_hint and _STANDARD_PATTERN.search(unit_hint.lower()):
        return "air" in unit_hint.lower()
    return False


def _column_lookup(columns: Iterable[str]) -> dict[str, str]:
    """Map normalised column names to their original dataframe labels."""

    lookup: dict[str, str] = {}
    for column in columns:
        key, _ = _normalise_header(column)
        if key and key not in lookup:
            lookup[key] = column
    return lookup


def _extract_first_value(series: pd.Series) -> str | float | int | None:
    """Return the first non-null, non-empty value from a series."""

    filtered = series.dropna()
    if filtered.empty:
        return None
    value = filtered.iloc[0]
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return None
        lowered = trimmed.lower()
        if lowered in {"nan", "none", "null"}:
            return None
        return trimmed
    if pd.isna(value):
        return None
    return value


def _select_column(column_lookup: dict[str, str], aliases: Iterable[str]) -> str | None:
    for alias in aliases:
        column = column_lookup.get(alias)
        if column:
            return column
    return None


def _build_metadata(df: pd.DataFrame, column_lookup: dict[str, str]) -> TraceMetadata:
    metadata = TraceMetadata()
    for key, aliases in _METADATA_ALIAS_MAP.items():
        original = _select_column(column_lookup, aliases)
        if original is None or original not in df.columns:
            continue
        value = _extract_first_value(df[original])
        if value is None:
            continue
        metadata.extra[key] = value
    metadata.target = metadata.extra.get("target") or metadata.extra.get("object")
    metadata.instrument = metadata.extra.get("instrument")
    metadata.telescope = metadata.extra.get("telescope")
    return metadata


_LABEL_PRIORITY = tuple(
    dict.fromkeys(
        _METADATA_ALIAS_MAP.get("target", ()) + _METADATA_ALIAS_MAP.get("object", ()) + ("name",)
    )
)


def _infer_label(
    df: pd.DataFrame, filename: str, column_lookup: dict[str, str] | None = None
) -> str:
    lookup = column_lookup or _column_lookup(df.columns)
    for candidate in _LABEL_PRIORITY:
        column = lookup.get(candidate)
        if not column:
            continue
        value = _extract_first_value(df[column])
        if value is not None:
            return str(value)
    stem = filename.rsplit("/", 1)[-1]
    return stem.split(".")[0]


def _is_numeric_token(token: str) -> bool:
    token = token.strip()
    if not token:
        return False
    try:
        float(token)
    except ValueError:
        return False
    return True


def _looks_like_headerless(df: pd.DataFrame) -> bool:
    if df.empty or not len(df.columns):
        return False
    tokens = [str(column) for column in df.columns]
    numeric_like = sum(_is_numeric_token(token) for token in tokens)
    unnamed_like = sum(token.lower().startswith("unnamed") for token in tokens)
    if numeric_like == len(tokens):
        return True
    return numeric_like + unnamed_like >= len(tokens)


def _numeric_column_stats(
    df: pd.DataFrame, *, ensure: Iterable[str] | None = None
) -> list[_NumericStats]:
    ensured = set(ensure or ())
    stats: list[_NumericStats] = []
    for column in df.columns:
        series = pd.to_numeric(df[column], errors="coerce")
        total = len(series)
        if total == 0:
            continue
        valid = series.dropna()
        coverage = len(valid) / total if total else 0.0
        if valid.empty:
            if column in ensured:
                stats.append(_NumericStats(column, coverage, 0.0, 0.0))
            continue
        if coverage < 0.4 and column not in ensured:
            continue
        values = valid.to_numpy(dtype=float)
        if values.size > 1:
            diffs = np.diff(values)
            if diffs.size:
                positive = float((diffs > 0).sum()) / diffs.size
                negative = float((diffs < 0).sum()) / diffs.size
                monotonic = max(positive, negative)
            else:
                monotonic = 0.0
            span = float(abs(values[-1] - values[0]))
        else:
            monotonic = 0.0
            span = 0.0
        stats.append(_NumericStats(column, coverage, monotonic, span))
    return stats


def _choose_wave_column(stats: list[_NumericStats], existing: str | None) -> str:
    if existing:
        return existing
    if not stats:
        raise ASCIIIngestError("No wavelength column detected")
    monotonic = [
        candidate for candidate in stats if candidate.monotonic >= 0.6 and candidate.span > 0.0
    ]
    if monotonic:
        ranked = sorted(
            monotonic,
            key=lambda item: (item.monotonic, item.coverage, item.span),
            reverse=True,
        )
        return ranked[0].column
    ranked = sorted(stats, key=lambda item: (item.coverage, item.span), reverse=True)
    return ranked[0].column


def _choose_flux_column(stats: list[_NumericStats], wave_column: str, existing: str | None) -> str:
    if existing:
        return existing
    candidates = [item for item in stats if item.column != wave_column]
    if not candidates:
        raise ASCIIIngestError("No flux/intensity column detected")
    ranked = sorted(
        candidates,
        key=lambda item: (item.coverage, -abs(item.monotonic - 0.5), item.span),
        reverse=True,
    )
    return ranked[0].column


@overload
def _to_numeric_array(series: pd.Series, *, allow_empty: Literal[False] = False) -> np.ndarray: ...


@overload
def _to_numeric_array(series: pd.Series, *, allow_empty: Literal[True]) -> np.ndarray | None: ...


def _to_numeric_array(series: pd.Series, *, allow_empty: bool = False) -> np.ndarray | None:
    numeric = pd.to_numeric(series, errors="coerce")
    valid_count = int(numeric.notna().sum())
    if valid_count == 0:
        if allow_empty:
            return None
        raise ASCIIIngestError(f"Column {series.name!r} contains no numeric data")
    return numeric.to_numpy(dtype=float)


def _read_ascii_dataframe(file_bytes: bytes) -> pd.DataFrame:
    text = file_bytes.decode("utf-8", errors="replace")
    buffer = io.StringIO(text)
    try:
        df = pd.read_csv(buffer, comment="#", sep=None, engine="python").dropna(how="all")
    except Exception as exc:  # pragma: no cover - surfaced in tests
        raise ASCIIIngestError(f"Failed to parse ASCII spectrum: {exc}") from exc

    if df.empty:
        return df

    df.columns = [str(column) for column in df.columns]

    if _looks_like_headerless(df):
        buffer.seek(0)
        df = pd.read_csv(
            buffer,
            comment="#",
            sep=None,
            engine="python",
            header=None,
        ).dropna(how="all")
        df.columns = [f"column_{index}" for index in range(len(df.columns))]

    df.columns = [str(column) for column in df.columns]
    return df


def _resolve_data_columns(
    df: pd.DataFrame,
) -> tuple[str, str, str | None, str]:
    infos = _describe_columns(df.columns)
    uncertainty_column = _detect_column(
        infos,
        _UNCERTAINTY_ALIASES,
        preferred_tokens=_FLUX_PREFERRED_TOKENS,
    )
    wave_column = _detect_column(
        infos,
        _WAVE_ALIASES,
        exclude=[uncertainty_column] if uncertainty_column else None,
        preferred_tokens=_WAVE_PREFERRED_TOKENS,
        penalty_tokens=_AMBIGUOUS_TOKENS,
    )
    flux_column = _detect_column(
        infos,
        _FLUX_ALIASES,
        exclude=[column for column in (wave_column, uncertainty_column) if column],
        preferred_tokens=_FLUX_PREFERRED_TOKENS,
        penalty_tokens=_AMBIGUOUS_TOKENS,
    )

    used_unit_hint = False
    wave_column, hinted = _apply_unit_hint(
        wave_column,
        infos,
        _WAVE_UNIT_HINTS,
        exclude=[column for column in (flux_column, uncertainty_column) if column],
    )
    used_unit_hint |= hinted
    flux_column, hinted = _apply_unit_hint(
        flux_column,
        infos,
        _FLUX_UNIT_HINTS,
        exclude=[column for column in (wave_column, uncertainty_column) if column],
    )
    used_unit_hint |= hinted

    detection_method = "aliases"
    if wave_column is None or flux_column is None:
        detection_method = "numeric_heuristic"
        stats_source = df
        if uncertainty_column and uncertainty_column in df.columns:
            stats_source = df.drop(columns=[uncertainty_column])
        stats = _numeric_column_stats(
            stats_source,
            ensure=[column for column in (wave_column, flux_column) if column is not None],
        )
        if len(stats) < 2 and (wave_column is None or flux_column is None):
            raise ASCIIIngestError("No numeric columns detected")
        wave_column = _choose_wave_column(stats, wave_column)
        flux_column = _choose_flux_column(stats, wave_column, flux_column)
    elif used_unit_hint:
        detection_method = "unit_hint"

    if wave_column is None:
        raise ASCIIIngestError("No wavelength column detected")
    if flux_column is None:
        raise ASCIIIngestError("No flux/intensity column detected")

    return wave_column, flux_column, uncertainty_column, detection_method


def load_ascii_spectrum(file_bytes: bytes, filename: str) -> ASCIIIngestResult:
    """Load an ASCII spectrum and return the parsed arrays plus metadata."""

    if not file_bytes:
        raise ASCIIIngestError("Empty file provided")

    content_hash = hashlib.sha256(file_bytes).hexdigest()
    df = _read_ascii_dataframe(file_bytes)

    if df.empty:
        raise ASCIIIngestError("No rows detected in spectrum file")

    total_rows = int(len(df))
    headerless = all(str(column).startswith("column_") for column in df.columns)
    column_lookup = _column_lookup(df.columns)
    wave_column, flux_column, uncertainty_column, detection_method = _resolve_data_columns(df)

    wave_name, wave_unit = _normalise_header(wave_column)
    _, flux_unit = _normalise_header(flux_column)
    is_air = _detect_standard(wave_column, wave_unit)

    wavelength = _to_numeric_array(df[wave_column])
    flux = _to_numeric_array(df[flux_column])
    valid_mask = np.isfinite(wavelength) & np.isfinite(flux)
    if not np.any(valid_mask):
        raise ASCIIIngestError("No overlapping numeric data between wavelength and flux columns")
    if not np.all(valid_mask):
        wavelength = wavelength[valid_mask]
        flux = flux[valid_mask]
    retained_rows = int(valid_mask.sum())

    uncertainties = None
    if uncertainty_column is not None:
        uncertainty_values = _to_numeric_array(df[uncertainty_column], allow_empty=True)
        if uncertainty_values is not None:
            if not np.all(valid_mask):
                uncertainty_values = uncertainty_values[valid_mask]
            uncertainties = uncertainty_values

    metadata = _build_metadata(df, column_lookup)

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
                "detection_method": detection_method,
                "headerless": headerless,
                "rows_total": total_rows,
                "rows_retained": retained_rows,
                "hash": content_hash,
            },
        )
    ]

    label = _infer_label(df, filename, column_lookup)

    wave_header = _clean_header(str(wave_column))
    wavelength_unit = wave_unit or wave_name
    if not wavelength_unit or headerless or _is_numeric_token(wave_header):
        wavelength_unit = "unknown"

    return ASCIIIngestResult(
        label=label,
        wavelength=wavelength,
        wavelength_unit=wavelength_unit,
        flux=flux,
        flux_unit=flux_unit,
        uncertainties=uncertainties,
        metadata=metadata,
        provenance=provenance,
        is_air_wavelength=is_air,
        content_hash=content_hash,
    )


__all__ = ["ASCIIIngestError", "ASCIIIngestResult", "load_ascii_spectrum"]
