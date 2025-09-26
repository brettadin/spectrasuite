"""MAST archive adapter implementation."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

try:  # pragma: no cover - network path exercised in integration runs
    from astroquery.mast import Observations
except Exception:  # pragma: no cover - astroquery optional during tests
    Observations = None  # type: ignore[assignment]

from server.fetchers.models import Product
from server.providers import ProviderHit, ProviderQuery, register_provider

_SPECTRUM_TYPES = {"spectrum"}
_DOWNLOAD_ROOT = "https://mast.stsci.edu/api/v0.1/Download/file?uri={uri}"


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


def _to_str(value: Any) -> str | None:
    coerced = _coerce_scalar(value)
    if coerced is None:
        return None
    return str(coerced)


def _length_to_nm(value: Any) -> float | None:
    if isinstance(value, u.Quantity):
        try:
            return float(value.to(u.nm).value)
        except Exception:
            try:
                return float(value.to(u.m).value) * 1e9
            except Exception:
                return None
    numeric = _to_float(value)
    if numeric is None:
        return None
    if numeric <= 0:
        return None
    if numeric < 1e-2:  # assume metres
        return numeric * 1e9
    return numeric


def _wave_range(row: Table | Any) -> tuple[float, float] | None:
    em_min = _length_to_nm(_raw(row, "em_min"))
    em_max = _length_to_nm(_raw(row, "em_max"))
    if em_min is None or em_max is None:
        return None
    return (em_min, em_max)


def _resolution(row: Table | Any) -> float | None:
    for key in ("s_resolution", "resolution", "specres", "resolpower"):
        value = _to_float(_raw(row, key))
        if value is not None and value > 0:
            return value
    return None


def _collect_urls(row: Table | Any) -> dict[str, str]:
    urls: dict[str, str] = {}
    preview = _to_str(_raw(row, "jpegURL")) or _to_str(_raw(row, "previewURL"))
    if preview:
        urls["preview"] = preview
    product_url = _to_str(_raw(row, "dataURL"))
    if product_url:
        urls["product"] = product_url
    return urls


def _augment_with_product_list(urls: dict[str, str], obs_identifier: Any) -> None:
    if Observations is None:
        return
    try:
        product_table = Observations.get_product_list(obs_identifier)
    except Exception:  # pragma: no cover - network failure handled gracefully
        return
    if product_table is None:
        return
    for row in product_table:
        dtype = _to_str(_raw(row, "dataproduct_type"))
        if dtype is None or dtype.lower() not in _SPECTRUM_TYPES:
            continue
        product_type = _to_str(_raw(row, "productType"))
        if product_type and product_type.upper() not in {"SCIENCE", "CALIBRATION"}:
            continue
        data_uri = _to_str(_raw(row, "dataURI"))
        if not data_uri:
            continue
        urls.setdefault("download", _DOWNLOAD_ROOT.format(uri=data_uri))
        description = _to_str(_raw(row, "description"))
        if description:
            urls.setdefault("description", description)


def _extra_metadata(row: Table | Any) -> dict[str, Any]:
    fields = [
        "obs_collection",
        "instrument_name",
        "filters",
        "proposal_id",
        "proposal_pi",
        "t_exptime",
        "dataRights",
    ]
    extra: dict[str, Any] = {}
    for field in fields:
        value = _raw(row, field)
        if value is None:
            continue
        if field == "t_exptime":
            numeric = _to_float(value)
            if numeric is not None:
                extra[field] = numeric
            continue
        coerced = _coerce_scalar(value)
        if coerced is not None:
            extra[field] = coerced
    return extra


def _rows_to_products(rows: Table) -> Iterator[Product]:
    for row in rows:
        dtype = _to_str(_raw(row, "dataproduct_type"))
        if dtype is not None and dtype.lower() not in _SPECTRUM_TYPES:
            continue
        obs_identifier = _raw(row, "obsid")
        product_id = _to_str(obs_identifier) or _to_str(_raw(row, "obs_id"))
        if product_id is None:
            continue
        title = _to_str(_raw(row, "obs_title")) or _to_str(_raw(row, "target_name")) or product_id
        target = _to_str(_raw(row, "target_name"))
        ra = _to_float(_raw(row, "s_ra"), unit=u.deg)
        dec = _to_float(_raw(row, "s_dec"), unit=u.deg)
        wave_range = _wave_range(row)
        resolution = _resolution(row)
        pipeline_version = _to_str(_raw(row, "provenance_name")) or _to_str(
            _raw(row, "instrument_name")
        )
        urls = _collect_urls(row)
        if obs_identifier is not None:
            _augment_with_product_list(urls, obs_identifier)
        doi = _to_str(_raw(row, "data_doi")) or _to_str(_raw(row, "obs_doi"))
        citation = _to_str(_raw(row, "obs_collection"))
        yield Product(
            provider="MAST",
            product_id=product_id,
            title=title,
            target=target,
            ra=ra,
            dec=dec,
            wave_range_nm=wave_range,
            resolution_R=resolution,
            wavelength_standard="unknown",
            flux_units=_to_str(_raw(row, "flux_units")) or _to_str(_raw(row, "fluxunit")),
            pipeline_version=pipeline_version,
            urls=urls,
            citation=citation,
            doi=doi,
            extra=_extra_metadata(row),
        )


def _product_to_hit(product: Product) -> ProviderHit:
    telescope = (
        str(product.extra.get("obs_collection")) if product.extra.get("obs_collection") else None
    )
    instrument = (
        str(product.extra.get("instrument_name")) if product.extra.get("instrument_name") else None
    )
    extras: dict[str, Any] = {}
    if product.extra.get("filters"):
        extras["filters"] = product.extra.get("filters")
    if product.extra.get("proposal_id"):
        extras["proposal_id"] = product.extra.get("proposal_id")
    return ProviderHit(
        provider="MAST",
        product=product,
        telescope=telescope,
        instrument=instrument,
        wave_range_nm=product.wave_range_nm,
        preview_url=product.urls.get("preview"),
        download_url=product.urls.get("download") or product.urls.get("product"),
        extras=extras,
    )


def search_products(*, ra: float, dec: float, radius_arcsec: float = 5.0) -> Iterable[ProviderHit]:
    """Search the MAST archive for spectroscopic products."""

    if Observations is None:
        raise RuntimeError("astroquery.mast is not available")

    coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
    radius = radius_arcsec * u.arcsec
    try:
        table = Observations.query_region(coord, radius=radius)
    except Exception as exc:  # pragma: no cover - depends on network access
        raise RuntimeError("MAST query failed") from exc
    if table is None or len(table) == 0:
        return []
    products = tuple(_rows_to_products(table))
    return tuple(_product_to_hit(product) for product in products)


def search(query: ProviderQuery) -> Iterable[ProviderHit]:
    """Adapter entry point used by the provider registry."""

    coordinates = query.coordinates()
    if coordinates is None:
        return []
    ra, dec = coordinates
    radius = query.filters.get("mast_radius_arcsec") if query.filters else None
    if radius is None:
        radius = query.radius_arcsec or 5.0
    try:
        radius_value = float(radius)
    except (TypeError, ValueError):
        radius_value = 5.0
    return search_products(ra=ra, dec=dec, radius_arcsec=radius_value)


register_provider("MAST", search)


__all__ = ["search", "search_products"]
