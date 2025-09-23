"""MAST archive adapter placeholder."""

from __future__ import annotations

from collections.abc import Iterable

from server.fetchers.models import Product


def search_products(*, ra: float, dec: float, radius_arcsec: float = 5.0) -> Iterable[Product]:
    """Search the MAST archive (placeholder)."""

    raise NotImplementedError("MAST adapter pending future implementation")
