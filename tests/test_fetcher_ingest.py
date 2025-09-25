from __future__ import annotations

from pathlib import Path

from server.fetchers.ingest_product import ProductIngestError, ingest_product
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
