"""DOI resolver adapter returning curated archive products."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from typing import Any, cast

from server.fetchers.models import Product
from server.providers import ProviderHit, ProviderQuery, register_provider

_SAMPLE_DOIS: dict[str, dict[str, Any]] = {
    "10.17909/t9xx11": {
        "product_id": "123",
        "title": "HST/STIS calibrated spectrum",
        "target": "M31",
        "provider": "MAST",
        "ra": 10.6847083,
        "dec": 41.269065,
        "wave_range_nm": (100.0, 200.0),
        "resolution_R": 1200.0,
        "preview": "https://mast.stsci.edu/spectrum.jpg",
        "download": "https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:HLSP/test/spectrum.fits",
        "portal": "https://doi.org/10.17909/T9XX11",
        "pipeline_version": "CALSPEC v1",
    }
}


def _build_product(record: dict[str, Any]) -> Product:
    urls = {
        "download": str(record["download"]),
        "portal": str(record["portal"]),
        "preview": str(record["preview"]),
    }
    wave_range = cast(tuple[float, float], record["wave_range_nm"])
    product = Product(
        provider=str(record["provider"]),
        product_id=str(record["product_id"]),
        title=str(record["title"]),
        target=str(record["target"]),
        ra=float(cast(float, record["ra"])),
        dec=float(cast(float, record["dec"])),
        wave_range_nm=(float(wave_range[0]), float(wave_range[1])),
        resolution_R=float(cast(float, record["resolution_R"])),
        wavelength_standard="unknown",
        flux_units="erg s^-1 cm^-2 Å^-1",
        pipeline_version=str(record["pipeline_version"]),
        urls=urls,
        citation="Digital Object Identifier",
        doi="10.17909/T9XX11",
        extra={"source": "doi"},
    )
    return product


def search(query: ProviderQuery) -> Iterable[ProviderHit]:
    doi_candidate: str | None = None
    if query.filters:
        filter_value = query.filters.get("doi")
        if isinstance(filter_value, str):
            doi_candidate = filter_value.strip()
    if not doi_candidate and query.identifier.lower().startswith("10."):
        doi_candidate = query.identifier.strip()
    if not doi_candidate:
        return []
    record = _SAMPLE_DOIS.get(doi_candidate.lower())
    if record is None:
        return []
    product = _build_product(record)
    return [
        ProviderHit(
            provider="DOI",
            product=replace(product),
            telescope=None,
            instrument=None,
            wave_range_nm=product.wave_range_nm,
            preview_url=product.urls.get("preview"),
            download_url=product.urls.get("download") or product.urls.get("portal"),
            extras={"doi": product.doi},
        )
    ]


register_provider("DOI", search)


__all__ = ["search"]
