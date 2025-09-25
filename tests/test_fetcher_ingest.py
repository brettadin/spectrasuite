from __future__ import annotations

import io
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest
from astropy.io import fits

from server.fetchers.ingest_product import ProductIngestError, _merge_metadata, ingest_product
from server.models import CanonicalSpectrum
from server.fetchers.models import Product


def _fake_product() -> Product:
    return Product(
        provider="TestArchive",
        product_id="TEST123",
        title="Calibration Spectrum",
        target="Target A",
        ra=10.0,
        dec=-5.0,
        wave_range_nm=(100.0, 200.0),
        resolution_R=1200.0,
        wavelength_standard="vacuum",
        flux_units="erg s^-1 cm^-2 Å^-1",
        pipeline_version="v1.2.3",
        urls={
            "download": "https://example.com/spectrum.fits",
            "product": "https://example.com/spectrum",
            "portal": "https://example.com/portal",
        },
        citation="Example Collaboration",
        doi="10.1234/example",
        extra={"program": "demo"},
    )


def _fits_bytes_with_metadata() -> bytes:
    wavelengths = np.linspace(4000.0, 4004.0, 5)
    flux = np.linspace(1.0, 5.0, 5)
    columns = [
        fits.Column(name="WAVELENGTH", array=wavelengths, format="D", unit="angstrom"),
        fits.Column(name="FLUX", array=flux, format="D", unit="erg/s/cm2/A"),
    ]
    table_hdu = fits.BinTableHDU.from_columns(columns, name="SPECTRUM")
    header = table_hdu.header
    header["OBJECT"] = "FITS Target"
    header["RA"] = 123.45
    header["DEC"] = -54.321
    header["SPECSYS"] = "BARYCENT"
    header["BUNIT"] = "erg/s/cm2/A"
    buffer = io.BytesIO()
    fits.HDUList([fits.PrimaryHDU(), table_hdu]).writeto(buffer)
    return buffer.getvalue()


def test_ingest_product_updates_metadata() -> None:
    product = _fake_product()

    def fake_fetch(url: str) -> bytes:
        assert url == product.urls["download"]
        return Path("data/examples/example_spectrum.fits").read_bytes()

    spectrum = ingest_product(product, fetcher=fake_fetch)

    assert spectrum.metadata.provider == "TestArchive"
    assert spectrum.metadata.product_id == "TEST123"
    assert spectrum.metadata.urls["download"] == product.urls["download"]
    assert spectrum.metadata.citation == "Example Collaboration"
    assert spectrum.metadata.doi == "10.1234/example"
    assert spectrum.metadata.extra["program"] == "demo"
    assert spectrum.metadata.resolving_power is not None
    assert any(event.step == "fetch_archive_product" for event in spectrum.provenance)


def test_ingest_product_without_download_url() -> None:
    product = _fake_product()
    product.urls.clear()

    try:
        ingest_product(product, fetcher=lambda _: b"")
    except ProductIngestError as exc:
        assert "download URL" in str(exc)
    else:  # pragma: no cover - should not happen
        raise AssertionError("Expected ProductIngestError for missing download URL")


def test_ingest_product_falls_back_to_product_url() -> None:
    product = _fake_product()
    product.urls.pop("download")

    fetched: list[str] = []

    def fake_fetch(url: str) -> bytes:
        fetched.append(url)
        return Path("data/examples/example_spectrum.fits").read_bytes()

    ingest_product(product, fetcher=fake_fetch)

    assert fetched == [product.urls["product"]]


def test_merge_preserves_canonical_fits_metadata() -> None:
    product = _fake_product()
    product.provider = "ArchiveX"
    product.product_id = "ARCHIVEID"
    product.target = "Archive Target"
    product.ra = 1.23
    product.dec = 4.56
    product.wavelength_standard = "unknown"

    fits_payload = _fits_bytes_with_metadata()

    def fake_fetch(url: str) -> bytes:
        assert url == product.urls["download"]
        return fits_payload

    spectrum = ingest_product(product, fetcher=fake_fetch)

    assert spectrum.metadata.provider == "ArchiveX"
    assert spectrum.metadata.product_id == "ARCHIVEID"
    assert spectrum.metadata.target == "FITS Target"
    assert spectrum.metadata.ra == pytest.approx(123.45)
    assert spectrum.metadata.dec == pytest.approx(-54.321)
    assert spectrum.metadata.wavelength_standard == "vacuum"


def test_merge_metadata_initialises_missing_metadata() -> None:
    product = _fake_product()
    canonical = SimpleNamespace(source_hash="placeholder")

    _merge_metadata(cast(CanonicalSpectrum, canonical), product)

    assert hasattr(canonical, "metadata")
    assert canonical.metadata.provider == "TestArchive"
    assert canonical.metadata.product_id == "TEST123"
    assert canonical.metadata.wave_range_nm == (100.0, 200.0)
    assert canonical.metadata.resolving_power == pytest.approx(1200.0)
    assert canonical.metadata.urls["download"] == product.urls["download"]
    assert canonical.metadata.citation == "Example Collaboration"
