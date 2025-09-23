"""SDSS spectral fetcher placeholder."""

from __future__ import annotations

from server.fetchers.models import Product


def fetch_by_specobjid(specobjid: int) -> Product:
    raise NotImplementedError("SDSS adapter pending future implementation")


def fetch_by_plate(plate: int, mjd: int, fiber: int) -> Product:
    raise NotImplementedError("SDSS adapter pending future implementation")
