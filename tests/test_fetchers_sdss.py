from __future__ import annotations

from typing import Any

import numpy as np
from astropy.io import fits
from astropy.table import Table

from server.fetchers import sdss


def _make_spectrum() -> fits.HDUList:
    loglam = np.array([3.0, 3.0001, 3.0002], dtype=float)
    flux = np.array([1.0, 1.1, 0.9], dtype=float)
    ivar = np.array([1.0, 1.0, 1.0], dtype=float)
    data = np.empty(loglam.size, dtype=[("loglam", "f8"), ("flux", "f8"), ("ivar", "f8")])
    data["loglam"] = loglam
    data["flux"] = flux
    data["ivar"] = ivar
    table_hdu = fits.BinTableHDU(data=data, name="COADD")
    primary = fits.PrimaryHDU()
    return fits.HDUList([primary, table_hdu])


class _FakeSDSS:
    last_query_kwargs: dict[str, Any] | None = None
    last_query_sql: str | None = None
    last_query_sql_kwargs: dict[str, Any] | None = None
    last_spectrum_kwargs: dict[str, Any] | None = None

    @classmethod
    def reset(cls) -> None:
        cls.last_query_kwargs = None
        cls.last_query_sql = None
        cls.last_query_sql_kwargs = None
        cls.last_spectrum_kwargs = None

    @staticmethod
    def _metadata_table() -> Table:
        table = Table()
        table["specobjid"] = [1234567890]
        table["plate"] = [2345]
        table["mjd"] = [56789]
        table["fiberid"] = [321]
        table["fiberID"] = [321]
        table["ra"] = [150.0]
        table["dec"] = [2.3]
        table["class"] = ["STAR"]
        table["run2d"] = ["v5_7_0"]
        table["run1d"] = ["v5_7_0"]
        table["programname"] = ["legacy"]
        table["survey"] = ["sdss"]
        table["instrument"] = ["SDSS"]
        table["z"] = [0.001]
        return table

    @classmethod
    def query_specobj(cls, **kwargs):  # type: ignore[override]
        cls.last_query_kwargs = kwargs
        return cls._metadata_table()

    @classmethod
    def query_sql(cls, sql_query: str, **kwargs):  # type: ignore[override]
        cls.last_query_sql = sql_query
        cls.last_query_sql_kwargs = kwargs
        return cls._metadata_table()

    @classmethod
    def get_spectra(cls, **kwargs):  # type: ignore[override]
        cls.last_spectrum_kwargs = kwargs
        return [_make_spectrum()]


def test_sdss_fetch_by_specobjid(monkeypatch) -> None:
    monkeypatch.setattr(sdss, "SDSS", _FakeSDSS)
    _FakeSDSS.reset()

    product = sdss.fetch_by_specobjid(1234567890)

    assert product.provider == "SDSS"
    assert product.product_id == "1234567890"
    assert product.wave_range_nm is not None
    assert product.wave_range_nm[0] > 0
    assert product.resolution_R is not None and product.resolution_R > 0
    assert product.wavelength_standard == "vacuum"
    assert product.urls["download"].endswith("specobjid=1234567890")
    assert product.extra["plate"] == 2345
    assert product.extra["fiberid"] == 321
    assert _FakeSDSS.last_query_kwargs == {"specobjid": 1234567890}
    assert _FakeSDSS.last_spectrum_kwargs == {"specobjid": 1234567890}


def test_sdss_fetch_by_plate(monkeypatch) -> None:
    monkeypatch.setattr(sdss, "SDSS", _FakeSDSS)
    _FakeSDSS.reset()

    product = sdss.fetch_by_plate(plate=2345, mjd=56789, fiber=321)

    assert product.product_id == "1234567890"
    assert _FakeSDSS.last_query_kwargs == {"plate": 2345, "mjd": 56789, "fiberID": 321}
    assert _FakeSDSS.last_spectrum_kwargs == {"plate": 2345, "mjd": 56789, "fiberID": 321}


def test_sdss_search_spectra_class_filter(monkeypatch) -> None:
    monkeypatch.setattr(sdss, "SDSS", _FakeSDSS)
    _FakeSDSS.reset()

    products = list(
        sdss.search_spectra(
            ra=150.0,
            dec=2.3,
            radius_arcsec=45.0,
            limit=5,
            class_="STAR",
        )
    )

    assert products
    assert _FakeSDSS.last_query_sql is not None
    assert "TOP 5" in _FakeSDSS.last_query_sql
    assert "class IN ('STAR')" in _FakeSDSS.last_query_sql
    assert _FakeSDSS.last_spectrum_kwargs == {"specobjid": 1234567890}
