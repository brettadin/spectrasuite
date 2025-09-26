"""Provider registry and search fan-out helpers."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from server.fetchers.models import Product, ResolverResult


@dataclass(slots=True)
class ProviderQuery:
    """Parameters passed to provider search adapters."""

    identifier: str
    resolver: ResolverResult | None = None
    radius_arcsec: float | None = None
    limit: int | None = None
    filters: dict[str, Any] = field(default_factory=dict)

    def coordinates(self) -> tuple[float, float] | None:
        """Return the resolved coordinates when available."""

        if self.resolver is None:
            return None
        if self.resolver.ra is None or self.resolver.dec is None:
            return None
        return (self.resolver.ra, self.resolver.dec)


@dataclass(slots=True)
class ProviderHit:
    """A single search result from a provider."""

    provider: str
    product: Product
    telescope: str | None = None
    instrument: str | None = None
    wave_range_nm: tuple[float, float] | None = None
    preview_url: str | None = None
    download_url: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)


ProviderSearch = Callable[[ProviderQuery], Iterable[ProviderHit]]

_LOGGER = logging.getLogger(__name__)
_REGISTRY: dict[str, ProviderSearch] = {}
_DEFAULTS_LOADED = False


def register_provider(name: str, search: ProviderSearch, /) -> None:
    """Register a provider search function."""

    _REGISTRY[name] = search


def unregister_provider(name: str) -> None:
    """Remove a provider from the registry (primarily for tests)."""

    _REGISTRY.pop(name, None)


def _ensure_defaults_loaded() -> None:
    global _DEFAULTS_LOADED
    if _DEFAULTS_LOADED:
        return
    # Import adapters lazily to avoid circular imports and optional dependencies.
    from server.fetchers import doi, eso, mast, sdss  # noqa: F401

    _DEFAULTS_LOADED = True


def provider_names() -> tuple[str, ...]:
    """Return the names of registered providers."""

    _ensure_defaults_loaded()
    return tuple(_REGISTRY.keys())


def search_all(query: ProviderQuery, *, include: Iterable[str] | None = None) -> list[ProviderHit]:
    """Fan out the query to all registered providers with deduplication."""

    _ensure_defaults_loaded()

    selected = set(include) if include is not None else None
    hits: list[ProviderHit] = []
    seen: set[tuple[str, str]] = set()

    for name, search in _REGISTRY.items():
        if selected is not None and name not in selected:
            continue
        try:
            results = list(search(query))
        except Exception as exc:
            _LOGGER.warning("Provider %s search failed: %s", name, exc)
            continue
        for hit in results:
            product = hit.product
            product_id = product.product_id or product.title or ""
            key = (product.provider or hit.provider or name, product_id)
            if not product_id:
                key = (product.provider or hit.provider or name, str(id(product)))
            if key in seen:
                continue
            seen.add(key)
            if hit.wave_range_nm is None:
                hit.wave_range_nm = product.wave_range_nm
            if hit.download_url is None:
                hit.download_url = (
                    product.urls.get("download")
                    or product.urls.get("product")
                    or product.urls.get("portal")
                )
            if hit.preview_url is None:
                hit.preview_url = product.urls.get("preview")
            hits.append(hit)
    return hits


__all__ = [
    "ProviderHit",
    "ProviderQuery",
    "provider_names",
    "register_provider",
    "search_all",
    "unregister_provider",
]
