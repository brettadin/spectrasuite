"""ESO archive adapter backed by curated sample metadata."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import replace
from typing import Any, cast

from server.fetchers.models import Product
from server.providers import ProviderHit, ProviderQuery, register_provider

_SAMPLE_DATA = [
    {
        "product_id": "ESO-UVES-001",
        "title": "VLT/UVES high-resolution spectrum",
        "target": "M31",
        "ra": 10.6847083,
        "dec": 41.269065,
        "wave_range_nm": (320.0, 1050.0),
        "resolution_R": 40000.0,
        "telescope": "VLT",
        "instrument": "UVES",
        "doi": "10.18727/ESO/SA-1234",
        "preview": "https://example.com/eso/uves_preview.jpg",
        "download": "https://archive.eso.org/datasets/eso-uves-001.fits",
        "pipeline_version": "6.0.1",
    },
    {
        "product_id": "ESO-XSH-002",
        "title": "VLT/X-shooter medium-resolution spectrum",
        "target": "M31",
        "ra": 10.6847083,
        "dec": 41.269065,
        "wave_range_nm": (300.0, 2480.0),
        "resolution_R": 7500.0,
        "telescope": "VLT",
        "instrument": "X-shooter",
        "doi": "10.18727/ESO/SA-5678",
        "preview": "https://example.com/eso/xshooter_preview.jpg",
        "download": "https://archive.eso.org/datasets/eso-xshooter-002.fits",
        "pipeline_version": "3.5.0",
    },
]


def _build_product(entry: dict[str, Any]) -> Product:
    urls = {
        "download": str(entry["download"]),
        "portal": "https://archive.eso.org/scienceportal/home",
        "preview": str(entry["preview"]),
    }
    extra = {
        "telescope": entry["telescope"],
        "instrument": entry["instrument"],
    }
    wave_range = cast(tuple[float, float], entry["wave_range_nm"])
    product = Product(
        provider="ESO",
        product_id=str(entry["product_id"]),
        title=str(entry["title"]),
        target=str(entry["target"]),
        ra=float(cast(float, entry["ra"])),
        dec=float(cast(float, entry["dec"])),
        wave_range_nm=(float(wave_range[0]), float(wave_range[1])),
        resolution_R=float(cast(float, entry["resolution_R"])),
        wavelength_standard="vacuum",
        flux_units="erg s^-1 cm^-2 Å^-1",
        pipeline_version=str(entry["pipeline_version"]),
        urls=urls,
        citation="ESO Science Archive",
        doi=str(entry["doi"]),
        extra=extra,
    )
    return product


def _hit_from_product(product: Product) -> ProviderHit:
    return ProviderHit(
        provider="ESO",
        product=replace(product),
        telescope=str(product.extra.get("telescope")) if product.extra.get("telescope") else None,
        instrument=(
            str(product.extra.get("instrument")) if product.extra.get("instrument") else None
        ),
        wave_range_nm=product.wave_range_nm,
        preview_url=product.urls.get("preview"),
        download_url=product.urls.get("download"),
        extras={"doi": product.doi},
    )


def _within_radius(
    entry: dict[str, object], coordinates: tuple[float, float], radius_arcsec: float
) -> bool:
    ra, dec = coordinates
    dra = float(cast(float, entry["ra"])) - ra
    dec_entry = float(cast(float, entry["dec"]))
    dec_avg = math.radians((dec_entry + dec) / 2.0)
    separation_deg = math.hypot(dra * math.cos(dec_avg), dec_entry - dec)
    return separation_deg <= radius_arcsec / 3600.0


def _normalise_filter(value: object | None) -> set[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return {cleaned.lower()} if cleaned else None
    if isinstance(value, Iterable):
        normalised = {str(item).strip().lower() for item in value if str(item).strip()}
        return normalised or None
    return {str(value).strip().lower()}


def search(query: ProviderQuery) -> Iterable[ProviderHit]:
    coordinates = query.coordinates()
    if coordinates is None:
        return []

    radius = query.radius_arcsec if query.radius_arcsec is not None else 20.0
    try:
        radius_value = float(radius)
    except (TypeError, ValueError):
        radius_value = 20.0

    instrument_filter = (
        _normalise_filter(query.filters.get("eso_instrument")) if query.filters else None
    )
    telescope_filter = (
        _normalise_filter(query.filters.get("eso_telescope")) if query.filters else None
    )
    hits: list[ProviderHit] = []
    for entry in _SAMPLE_DATA:
        if not _within_radius(entry, coordinates, radius_value):
            continue
        if instrument_filter and str(entry["instrument"]).lower() not in instrument_filter:
            continue
        if telescope_filter and str(entry["telescope"]).lower() not in telescope_filter:
            continue
        hits.append(_hit_from_product(_build_product(entry)))
    return hits


register_provider("ESO", search)


__all__ = ["search"]
