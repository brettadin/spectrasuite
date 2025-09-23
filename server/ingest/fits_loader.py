"""FITS spectrum ingestion utilities."""

from __future__ import annotations

import hashlib
import io
import numbers
from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Literal

import numpy as np
from astropy.io import fits

from server.models import ProvenanceEvent, TraceMetadata

_WAVE_COLUMN_ALIASES = {
    "wavelength",
    "wavelength_nm",
    "lambda",
    "lambda_nm",
    "wave",
    "wl",
    "lam",
    "loglam",
}

_LOG_WAVE_COLUMNS = {"loglam"}

_FLUX_COLUMN_ALIASES = {
    "flux",
    "flux_density",
    "intensity",
    "flux_erg",
    "flux_jy",
}

_UNCERTAINTY_ALIASES = {"uncertainty", "unc", "sigma", "error", "err"}

_UNCERTAINTY_HDU_NAMES = {"ERR", "ERROR", "UNC", "UNCERTAINTY", "SIG", "SIGMA"}


@dataclass(slots=True)
class FITSIngestResult:
    """Parsed FITS spectrum and accompanying metadata."""

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


class FITSIngestError(RuntimeError):
    """Raised when FITS ingestion fails."""


def load_fits_spectrum(
    source: str | Path | BinaryIO, *, filename: str | None = None
) -> FITSIngestResult:
    """Load a 1D spectrum from a FITS file into the ingest model."""

    data_bytes, source_name = _read_source(source, filename)
    if not data_bytes:
        raise FITSIngestError("Empty FITS payload provided")

    content_hash = hashlib.sha256(data_bytes).hexdigest()

    try:
        with fits.open(io.BytesIO(data_bytes), memmap=False) as hdul:
            index, spectrum_hdu = _select_spectrum_hdu(hdul)
            wavelength, wave_unit, wcs_params = _extract_wavelength(spectrum_hdu)
            flux, flux_unit = _extract_flux(spectrum_hdu)
            uncertainties = _extract_uncertainties(hdul, index, flux.size)
            is_air = _detect_air_wavelength(spectrum_hdu.header, wave_unit)
            metadata = _build_metadata(spectrum_hdu.header)
    except OSError as exc:  # pragma: no cover - astropy error handling
        raise FITSIngestError(f"Failed to read FITS file: {exc}") from exc

    metadata.extra.setdefault("wcs", wcs_params)
    provenance = [
        ProvenanceEvent(
            step="ingest_fits",
            parameters={
                "filename": source_name,
                "hdu_index": index,
                "extname": spectrum_hdu.name.strip() or "PRIMARY",
                "flux_unit": flux_unit or metadata.flux_units or "unknown",
                "wavelength_unit": wave_unit,
                "is_air": is_air,
                "hash": content_hash,
                "wcs": wcs_params,
            },
        )
    ]

    label = metadata.target or Path(source_name).stem or "FITS Spectrum"

    return FITSIngestResult(
        label=label,
        wavelength=wavelength,
        wavelength_unit=wave_unit,
        flux=flux,
        flux_unit=flux_unit or metadata.flux_units,
        uncertainties=uncertainties,
        metadata=metadata,
        provenance=provenance,
        is_air_wavelength=is_air,
        content_hash=content_hash,
    )


def _read_source(source: str | Path | BinaryIO, filename: str | None) -> tuple[bytes, str]:
    if isinstance(source, str) or isinstance(source, Path):
        path = Path(source)
        return path.read_bytes(), path.name
    raw = source.read()
    if hasattr(source, "seek"):
        with suppress(OSError, ValueError):
            source.seek(0)
    name = filename or getattr(source, "name", "stream")
    return raw, str(name)


def _select_spectrum_hdu(hdul: fits.HDUList) -> tuple[int, fits.hdu.base.ExtensionHDU]:
    for index, hdu in enumerate(hdul):
        data = hdu.data
        if data is None:
            continue
        if isinstance(data, fits.FITS_rec):
            columns = _normalise_names(hdu.columns.names or [])
            if columns & _FLUX_COLUMN_ALIASES:
                return index, hdu
        else:
            array = np.asarray(data)
            if array.ndim == 1 or (array.ndim == 2 and 1 in array.shape):
                return index, hdu
    raise FITSIngestError("No 1D spectral data found in FITS file")


def _extract_flux(hdu: fits.hdu.base.ExtensionHDU) -> tuple[np.ndarray, str | None]:
    data = hdu.data
    if isinstance(data, fits.FITS_rec):
        columns = list(hdu.columns.names or [])
        column = _match_column(columns, _FLUX_COLUMN_ALIASES)
        if column is None:
            raise FITSIngestError("FITS table is missing a flux column")
        flux_unit = _clean_unit(hdu.columns[column].unit)
        flux = np.asarray(data[column], dtype=float)
        return flux, flux_unit
    flux = np.asarray(data, dtype=float).reshape(-1)
    flux_unit = _clean_unit(hdu.header.get("BUNIT"))
    return flux, flux_unit


def _extract_wavelength(
    hdu: fits.hdu.base.ExtensionHDU,
) -> tuple[np.ndarray, str, dict[str, float | str | None]]:
    data = hdu.data
    header = hdu.header
    if isinstance(data, fits.FITS_rec):
        columns = list(hdu.columns.names or [])
        column = _match_column(columns, _WAVE_COLUMN_ALIASES)
        if column is None:
            raise FITSIngestError("FITS table is missing a wavelength column")
        values = np.asarray(data[column], dtype=float)
        unit = _clean_unit(hdu.columns[column].unit) or _clean_unit(header.get("CUNIT1"))
        if column.lower() in _LOG_WAVE_COLUMNS:
            values = np.power(10.0, values)
            unit = unit or "angstrom"
        return values, unit or "unknown", {}

    array = np.asarray(data, dtype=float).reshape(-1)
    wcs_params = _wcs_parameters(header)
    if wcs_params is None:
        raise FITSIngestError("FITS image lacks WCS dispersion keywords")
    crval1, cdelt1, crpix1, ctype1, unit = wcs_params
    pixels = np.arange(array.size, dtype=float)
    wavelengths = crval1 + (pixels + 1 - crpix1) * cdelt1
    ctype_upper = ctype1.upper()
    if ctype_upper.startswith("LOG"):
        wavelengths = np.power(10.0, wavelengths)
        unit = unit or "angstrom"
    return (
        wavelengths,
        unit or "unknown",
        {
            "CRVAL1": crval1,
            "CDELT1": cdelt1,
            "CRPIX1": crpix1,
            "CTYPE1": ctype1,
            "CUNIT1": unit,
        },
    )


def _extract_uncertainties(hdul: fits.HDUList, skip_index: int, length: int) -> np.ndarray | None:
    for index, hdu in enumerate(hdul):
        if index == skip_index:
            continue
        data = hdu.data
        if data is None:
            continue
        if isinstance(data, fits.FITS_rec):
            columns = list(hdu.columns.names or [])
            column = _match_column(columns, _UNCERTAINTY_ALIASES)
            if column is not None:
                uncertainties = np.asarray(data[column], dtype=float).reshape(-1)
                if uncertainties.size == length:
                    return uncertainties
        else:
            if (hdu.name or "").strip().upper() not in _UNCERTAINTY_HDU_NAMES:
                continue
            uncertainties = np.asarray(data, dtype=float).reshape(-1)
            if uncertainties.size == length:
                return uncertainties
    return None


def _detect_air_wavelength(header: fits.Header, unit: str | None) -> bool:
    ctype1 = str(header.get("CTYPE1", "")).strip().upper()
    if ctype1.startswith("AWAV"):
        return True
    if ctype1.startswith("WAVE"):
        return False
    airorvac = str(header.get("AIRORVAC", "")).strip().lower()
    if airorvac == "air":
        return True
    if airorvac == "vac" or airorvac == "vacuum":
        return False
    vacuum_flag = str(header.get("VACUUM", "")).strip().upper()
    if vacuum_flag == "F":
        return True
    if vacuum_flag == "T":
        return False
    return bool(unit and "air" in unit.lower())


def _build_metadata(header: fits.Header) -> TraceMetadata:
    specsys_raw = _clean_str(header.get("SPECSYS"))
    metadata = TraceMetadata(
        target=_clean_str(header.get("OBJECT")),
        instrument=_clean_str(header.get("INSTRUME")),
        telescope=_clean_str(header.get("TELESCOP")),
        flux_units=_clean_unit(header.get("BUNIT")),
        pipeline_version=_clean_str(
            header.get("PIPEVER")
            or header.get("PROCVERS")
            or header.get("VERSION")
            or header.get("PIPELINE")
        ),
        frame=_normalise_frame(specsys_raw),
        radial_velocity_kms=_safe_float(
            header.get("VRAD") or header.get("VHELIO") or header.get("RADVEL")
        ),
    )
    metadata.ra = _safe_float(header.get("RA") or header.get("OBJRA"))
    metadata.dec = _safe_float(header.get("DEC") or header.get("OBJDEC"))
    metadata.resolving_power = _safe_float(
        header.get("R") or header.get("RVAL") or header.get("RESOLUT")
    )
    metadata.extra.update(
        {
            "observer": _clean_str(header.get("OBSERVER")),
            "exposure_time": _safe_float(header.get("EXPTIME")),
            "date_obs": _clean_str(header.get("DATE-OBS")),
        }
    )
    if specsys_raw and metadata.frame is None:
        metadata.extra["original_frame"] = specsys_raw
    return metadata


def _match_column(columns: Iterable[str], aliases: set[str]) -> str | None:
    for name in columns:
        if name is None:
            continue
        if name.lower() in aliases:
            return name
    return None


def _normalise_names(columns: Iterable[str]) -> set[str]:
    return {name.lower() for name in columns if name}


def _clean_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    text = str(unit).strip()
    return text or None


def _clean_str(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_float(value: object | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, numbers.Real):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _normalise_frame(
    value: str | None,
) -> Literal["topocentric", "heliocentric", "barycentric", "unknown", "none"] | None:
    if value is None:
        return None
    lookup: dict[str, Literal["topocentric", "heliocentric", "barycentric"]] = {
        "TOPOCENT": "topocentric",
        "GEOCENTR": "topocentric",
        "HELIOCEN": "heliocentric",
        "HELIOCENTRIC": "heliocentric",
        "BARYCENT": "barycentric",
        "BARYCENTRIC": "barycentric",
    }
    upper = value.upper()
    if upper in lookup:
        return lookup[upper]
    lower = value.lower()
    if lower == "unknown":
        return "unknown"
    if lower == "none":
        return "none"
    return None


def _wcs_parameters(
    header: fits.Header,
) -> tuple[float, float, float, str, str | None] | None:
    crval1 = _safe_float(header.get("CRVAL1"))
    cdelt1 = _safe_float(header.get("CDELT1") or header.get("CD1_1"))
    crpix1 = _safe_float(header.get("CRPIX1")) or 1.0
    ctype1 = _clean_str(header.get("CTYPE1")) or ""
    unit = _clean_unit(header.get("CUNIT1") or header.get("XUNIT"))
    if crval1 is None or cdelt1 is None:
        return None
    return crval1, cdelt1, crpix1, ctype1, unit


__all__ = ["FITSIngestError", "FITSIngestResult", "load_fits_spectrum"]
