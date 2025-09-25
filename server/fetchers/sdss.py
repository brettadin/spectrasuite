"""SDSS spectral fetcher implementation."""

from __future__ import annotations

import textwrap
from collections.abc import Iterable
from contextlib import suppress
from string import Template
from typing import Any

import numpy as np
from astropy import units as u
from astropy.io import fits
from astropy.table import Table

try:  # pragma: no cover - network exercised separately
    from astroquery.sdss import SDSS
except Exception:  # pragma: no cover - astroquery optional during tests
    SDSS = None  # type: ignore[assignment]

from server.fetchers.models import Product

_FLUX_UNITS = "1e-17 erg s^-1 cm^-2 Å^-1"


def _is_masked(value: Any) -> bool:
    mask = getattr(value, "mask", None)
    if mask is None:
        return False
    if mask is np.ma.nomask:  # type: ignore[attr-defined]
        return False
    try:
        return bool(np.all(mask))
    except Exception:
        return bool(mask)


def _raw(row: Table | Any, key: str) -> Any | None:
    if key not in getattr(row, "colnames", []):
        return None
    value = row[key]
    if _is_masked(value):
        return None
    return value


def _coerce_scalar(value: Any) -> Any | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, np.generic):
        return value.item()
    if hasattr(value, "item") and not isinstance(value, str | bytes):
        size = getattr(value, "size", None)
        if size == 1:
            return value.item()
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return value


def _to_float(value: Any, *, unit: u.Unit | None = None) -> float | None:
    if value is None:
        return None
    if isinstance(value, u.Quantity):
        try:
            if unit is not None:
                return float(value.to(unit).value)
            return float(value.to_value())
        except Exception:
            return None
    coerced = _coerce_scalar(value)
    if coerced is None:
        return None
    try:
        result = float(coerced)
    except (TypeError, ValueError):
        return None
    if np.isnan(result):
        return None
    return result


def _to_int(value: Any) -> int | None:
    numeric = _to_float(value)
    if numeric is None:
        return None
    return int(round(numeric))


def _to_str(value: Any) -> str | None:
    coerced = _coerce_scalar(value)
    if coerced is None:
        return None
    return str(coerced)


def _extract_wave_range(hdul: fits.HDUList) -> tuple[float, float] | None:
    for key in ("COADD", 1):
        if key not in hdul:
            continue
        data = hdul[key].data
        if data is None or "loglam" not in data.dtype.names:
            continue
        loglam = np.array(data["loglam"], dtype=float)
        if loglam.size == 0:
            continue
        lam_angstrom = np.power(10.0, loglam)
        lam_nm = lam_angstrom * 0.1
        return (float(np.min(lam_nm)), float(np.max(lam_nm)))
    return None


def _estimate_resolution(hdul: fits.HDUList) -> float | None:
    for key in ("COADD", 1):
        if key not in hdul:
            continue
        data = hdul[key].data
        if data is None or "loglam" not in data.dtype.names:
            continue
        loglam = np.array(data["loglam"], dtype=float)
        if loglam.size < 2:
            continue
        diffs = np.diff(loglam)
        positive = diffs[diffs > 0]
        if positive.size == 0:
            continue
        delta_log = float(np.median(positive))
        lam_angstrom = float(np.median(np.power(10.0, loglam)))
        delta_lambda = lam_angstrom * np.log(10.0) * delta_log
        if delta_lambda <= 0:
            continue
        return lam_angstrom / delta_lambda
    return None


def _close_all(hdul_list: Iterable[fits.HDUList]) -> None:
    for hdul in hdul_list:
        with suppress(Exception):  # pragma: no cover - defensive close
            hdul.close()


def _load_spectrum(**kwargs: Any) -> fits.HDUList:
    if SDSS is None:
        raise RuntimeError("astroquery.sdss is not available")
    spectra = SDSS.get_spectra(**kwargs)
    if not spectra:
        raise LookupError("No spectra available for the requested target")
    hdul = spectra[0]
    # close any extra HDUs that may have been returned beyond the first
    _close_all(spectra[1:])
    return hdul


def _query_specobj(**kwargs: Any) -> Table:
    if SDSS is None:
        raise RuntimeError("astroquery.sdss is not available")
    table = SDSS.query_specobj(**kwargs)
    if table is None or len(table) == 0:
        raise LookupError("No SDSS metadata found for the requested target")
    return table


def _normalise_class_filter(
    value: str | Iterable[str] | None,
) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        candidates = [value]
    else:
        candidates = list(value)
    normalised: list[str] = []
    for item in candidates:
        if item is None:
            continue
        text = str(item).strip()
        if not text:
            continue
        normalised.append(text.replace("'", "''"))
    return normalised


def search_spectra(
    *,
    ra: float,
    dec: float,
    radius_arcsec: float = 30.0,
    limit: int = 10,
    class_: str | Iterable[str] | None = None,
    class_filter: str | Iterable[str] | None = None,
) -> Iterable[Product]:
    """Search for SDSS spectra near coordinates."""

    if SDSS is None:
        raise RuntimeError("astroquery.sdss is not available")

    radius_arcmin = _normalise_radius(radius_arcsec)
    if radius_arcmin is None:
        return []

    max_results = _normalise_limit(limit)
    if max_results is None:
        return []

    ra_value, dec_value = _coerce_coordinates(ra, dec)
    filter_values = _select_filters(class_, class_filter)
    class_clause = _build_class_clause(filter_values)
    sql = _build_search_sql(max_results, ra_value, dec_value, radius_arcmin, class_clause)

    table = SDSS.query_sql(sql)
    if table is None or len(table) == 0:
        return []

    return _iter_products(table)


def _normalise_radius(radius_arcsec: float) -> float | None:
    try:
        radius = float(radius_arcsec)
    except (TypeError, ValueError):
        return None
    if radius <= 0:
        return None
    radius_arcmin = radius / 60.0
    return min(radius_arcmin, 3.0)


def _normalise_limit(limit: int) -> int | None:
    try:
        max_results = int(limit)
    except (TypeError, ValueError):
        return None
    if max_results <= 0:
        return None
    return max_results


def _coerce_coordinates(ra: float, dec: float) -> tuple[float, float]:
    try:
        ra_value = float(ra)
        dec_value = float(dec)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive guard
        raise ValueError("RA and Dec must be finite floats") from exc
    return ra_value, dec_value


def _select_filters(
    class_: str | Iterable[str] | None, class_filter: str | Iterable[str] | None
) -> tuple[str, ...]:
    primary = tuple(_normalise_class_filter(class_))
    if primary:
        return primary
    return tuple(_normalise_class_filter(class_filter))


def _build_class_clause(filter_values: tuple[str, ...]) -> str:
    if not filter_values:
        return ""
    joined = ", ".join(f"'{item}'" for item in filter_values)
    return f" AND s.class IN ({joined})"


def _build_search_sql(
    max_results: int,
    ra_value: float,
    dec_value: float,
    radius_arcmin: float,
    class_clause: str,
) -> str:
    template = Template(
        textwrap.dedent(
            """
            SELECT TOP $max_results
                s.specObjID AS specobjid,
                s.ra,
                s.dec,
                s.plate,
                s.mjd,
                s.fiberID,
                s.run2d,
                s.run1d,
                s.programname,
                s.survey,
                s.instrument,
                s.class,
                s.z
            FROM SpecObjAll AS s
            JOIN dbo.fGetNearbySpecObjEq($ra_value, $dec_value, $radius_arcmin) AS nearby
                ON nearby.specObjID = s.specObjID
            WHERE s.sciencePrimary = 1$class_clause
            ORDER BY nearby.distance
            """
        ).strip()
    )
    substitutions = {
        "max_results": max_results,
        "ra_value": f"{ra_value:.8f}",
        "dec_value": f"{dec_value:.8f}",
        "radius_arcmin": f"{radius_arcmin:.6f}",
        "class_clause": class_clause,
    }
    return template.substitute(substitutions)


def _iter_products(table: Table) -> Iterable[Product]:
    def _iterator() -> Iterable[Product]:
        for row in table:  # pragma: no branch - simple iteration
            specobjid = _to_int(_raw(row, "specobjid"))
            if specobjid is None:
                continue
            try:
                hdul = _load_spectrum(specobjid=specobjid)
            except LookupError:
                continue
            yield _build_product(row, hdul=hdul)

    return _iterator()


def _build_product(row: Any, *, hdul: fits.HDUList) -> Product:
    specobjid = _to_str(_raw(row, "specobjid"))
    if specobjid is None:
        raise LookupError("SpecObjID missing from SDSS metadata")
    wave_range = _extract_wave_range(hdul)
    resolution = _estimate_resolution(hdul)
    ra = _to_float(_raw(row, "ra"), unit=u.deg)
    dec = _to_float(_raw(row, "dec"), unit=u.deg)
    pipeline_version = _to_str(_raw(row, "run2d")) or _to_str(_raw(row, "run1d"))
    urls = {
        "portal": f"https://skyserver.sdss.org/dr17/en/tools/explore/summary.aspx?id={specobjid}",
        "download": f"https://dr17.sdss.org/api/spectrum?specobjid={specobjid}",
    }
    extra: dict[str, Any] = {}
    field_map = {
        "plate": "plate",
        "mjd": "mjd",
        "fiberid": "fiberid",
        "fiberID": "fiberid",
        "programname": "programname",
        "survey": "survey",
        "instrument": "instrument",
        "class": "class",
        "z": "z",
    }
    for source_key, target_key in field_map.items():
        if target_key in extra:
            continue
        value = _raw(row, source_key)
        if value is None:
            continue
        if target_key in {"plate", "mjd", "fiberid"}:
            numeric_int = _to_int(value)
            if numeric_int is not None:
                extra[target_key] = numeric_int
            continue
        numeric_float = _to_float(value)
        if numeric_float is not None and target_key == "z":
            extra[target_key] = numeric_float
            continue
        coerced = _coerce_scalar(value)
        if coerced is not None:
            extra[target_key] = coerced

    hdul.close()

    return Product(
        provider="SDSS",
        product_id=specobjid,
        title=f"SDSS spectrum {specobjid}",
        target=_to_str(_raw(row, "class")),
        ra=ra,
        dec=dec,
        wave_range_nm=wave_range,
        resolution_R=resolution,
        wavelength_standard="vacuum",
        flux_units=_FLUX_UNITS,
        pipeline_version=pipeline_version,
        urls=urls,
        citation="SDSS Collaboration",
        doi=None,
        extra=extra,
    )


def fetch_by_specobjid(specobjid: int) -> Product:
    """Fetch an SDSS spectrum by SpecObjID."""

    table = _query_specobj(specobjid=specobjid)
    row = table[0]
    hdul = _load_spectrum(specobjid=specobjid)
    return _build_product(row, hdul=hdul)


def fetch_by_plate(plate: int, mjd: int, fiber: int) -> Product:
    """Fetch an SDSS spectrum by plate/MJD/fiber identifier."""

    table = _query_specobj(plate=plate, mjd=mjd, fiberID=fiber)
    row = table[0]
    hdul = _load_spectrum(plate=plate, mjd=mjd, fiberID=fiber)
    return _build_product(row, hdul=hdul)


__all__ = ["search_spectra", "fetch_by_specobjid", "fetch_by_plate"]
