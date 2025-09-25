"""Utilities for downloading and ingesting archive products."""

from __future__ import annotations

import io
import urllib.parse
import urllib.request
from collections.abc import Callable

from server.fetchers.models import Product
from server.ingest.ascii_loader import ASCIIIngestError, load_ascii_spectrum
from server.ingest.canonicalize import canonicalize_ascii, canonicalize_fits
from server.ingest.fits_loader import FITSIngestError, load_fits_spectrum
from server.models import CanonicalSpectrum, ProvenanceEvent


class ProductIngestError(RuntimeError):
    """Raised when an archive product cannot be downloaded or ingested."""


def _default_fetcher(url: str) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ProductIngestError("Unsupported URL scheme for archive download")
    request = urllib.request.Request(url, headers={"User-Agent": "spectrasuite/1.0"})  # noqa: S310
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - trusted archives
        payload = response.read()
    if not payload:
        raise ProductIngestError("Archive returned an empty payload")
    return payload


def _filename_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    candidate = urllib.parse.unquote(parsed.path.rsplit("/", 1)[-1])
    return candidate or "archive_product"


def _merge_metadata(canonical: CanonicalSpectrum, product: Product) -> None:
    metadata = canonical.metadata

    metadata.provider = product.provider or metadata.provider
    metadata.product_id = product.product_id or metadata.product_id
    metadata.title = product.title or metadata.title
    metadata.target = product.target or metadata.target
    metadata.ra = product.ra if product.ra is not None else metadata.ra
    metadata.dec = product.dec if product.dec is not None else metadata.dec
    metadata.wave_range_nm = metadata.wave_range_nm or product.wave_range_nm
    if product.resolution_R is not None and metadata.resolving_power is None:
        metadata.resolving_power = product.resolution_R
    standard = product.wavelength_standard
    if standard == "none":
        metadata.wavelength_standard = None
    elif standard == "air":
        metadata.wavelength_standard = "air"
    elif standard == "vacuum":
        metadata.wavelength_standard = "vacuum"
    elif standard == "mixed":
        metadata.wavelength_standard = "unknown"
    if product.flux_units and not metadata.flux_units:
        metadata.flux_units = product.flux_units
    if product.pipeline_version and not metadata.pipeline_version:
        metadata.pipeline_version = product.pipeline_version
    metadata.urls.update(product.urls)
    metadata.citation = product.citation or metadata.citation
    metadata.doi = product.doi or metadata.doi
    metadata.extra.update(product.extra)


def ingest_product(
    product: Product, *, fetcher: Callable[[str], bytes] | None = None
) -> CanonicalSpectrum:
    """Download an archive product and convert it into a canonical spectrum."""

    download_url = product.urls.get("download") or product.urls.get("product")
    if not download_url:
        raise ProductIngestError("Product does not expose a download URL")

    fetch = fetcher or _default_fetcher
    try:
        payload = fetch(download_url)
    except Exception as exc:  # pragma: no cover - network errors surfaced to UI
        raise ProductIngestError(f"Failed to download archive product: {exc}") from exc

    if not payload:
        raise ProductIngestError("Archive returned an empty payload")

    filename_hint = _filename_from_url(download_url)

    try:
        ingest_result = load_fits_spectrum(io.BytesIO(payload), filename=filename_hint)
        canonical = canonicalize_fits(ingest_result)
    except FITSIngestError:
        try:
            ascii_result = load_ascii_spectrum(payload, filename_hint)
            canonical = canonicalize_ascii(ascii_result)
        except ASCIIIngestError as ascii_exc:
            raise ProductIngestError(
                "Archive product is not a supported FITS/ASCII spectrum"
            ) from ascii_exc

    canonical.label = (
        f"{product.provider}: {product.title}"
        if product.provider and product.title
        else product.title or product.product_id or canonical.label
    )

    _merge_metadata(canonical, product)
    canonical.provenance.append(
        ProvenanceEvent(
            step="fetch_archive_product",
            parameters={
                "provider": product.provider,
                "product_id": product.product_id,
                "url": download_url,
            },
            note="Downloaded from archive via Star Hub",
        )
    )

    return canonical


__all__ = ["ProductIngestError", "ingest_product"]
