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
from server.models import CanonicalSpectrum, ProvenanceEvent, TraceMetadata


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
    metadata = _ensure_metadata(canonical)
    _merge_provider(metadata, product)
    _merge_identifiers(metadata, canonical, product)
    _merge_target_and_pointing(metadata, product)
    _merge_spectral_characteristics(metadata, product)
    _merge_units_and_pipeline(metadata, product)
    _merge_references(metadata, product)


def _ensure_metadata(canonical: CanonicalSpectrum) -> TraceMetadata:
    metadata = getattr(canonical, "metadata", None)
    if isinstance(metadata, TraceMetadata):
        return metadata

    new_metadata = TraceMetadata()
    try:
        canonical.metadata = new_metadata  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - fallback for exotic objects
        object.__setattr__(canonical, "metadata", new_metadata)
    return new_metadata


def _merge_provider(metadata: TraceMetadata, product: Product) -> None:
    if product.provider and metadata.provider in {None, "upload"}:
        metadata.provider = product.provider


def _merge_identifiers(
    metadata: TraceMetadata, canonical: CanonicalSpectrum, product: Product
) -> None:
    if product.product_id:
        source_hash = getattr(canonical, "source_hash", None)
        placeholder_ids = {source_hash} if source_hash else set()
        if metadata.product_id is None or metadata.product_id in placeholder_ids:
            metadata.product_id = product.product_id
    if product.title and not metadata.title:
        metadata.title = product.title


def _merge_target_and_pointing(metadata: TraceMetadata, product: Product) -> None:
    if product.target and not metadata.target:
        metadata.target = product.target
    if metadata.ra is None and product.ra is not None:
        metadata.ra = product.ra
    if metadata.dec is None and product.dec is not None:
        metadata.dec = product.dec


def _merge_spectral_characteristics(metadata: TraceMetadata, product: Product) -> None:
    if metadata.wave_range_nm is None and product.wave_range_nm is not None:
        metadata.wave_range_nm = product.wave_range_nm
    if product.resolution_R is not None and metadata.resolving_power is None:
        metadata.resolving_power = product.resolution_R
    standard = product.wavelength_standard
    if metadata.wavelength_standard is None and standard is not None:
        if standard == "none":
            metadata.wavelength_standard = None
        elif standard == "air":
            metadata.wavelength_standard = "air"
        elif standard == "vacuum":
            metadata.wavelength_standard = "vacuum"
        elif standard == "mixed":
            metadata.wavelength_standard = "unknown"


def _merge_units_and_pipeline(metadata: TraceMetadata, product: Product) -> None:
    if product.flux_units and not metadata.flux_units:
        metadata.flux_units = product.flux_units
    if product.pipeline_version and not metadata.pipeline_version:
        metadata.pipeline_version = product.pipeline_version


def _merge_references(metadata: TraceMetadata, product: Product) -> None:
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
