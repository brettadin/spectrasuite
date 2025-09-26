from __future__ import annotations

import numpy as np
from streamlit.testing.v1 import AppTest

from app.state.session import AppSessionState
from server.fetchers.models import Product, ResolverResult
from server.models import CanonicalSpectrum, TraceMetadata
from server.providers import ProviderHit, ProviderQuery


def _render_star_hub(session) -> None:
    from app.ui.star_hub import render_star_hub_tab as _render

    _render(session)


def _resolver() -> ResolverResult:
    return ResolverResult(
        canonical_name="M31",
        ra=10.6847083,
        dec=41.269065,
        object_type="GALAXY",
        aliases=["Andromeda"],
        provenance={"source": "test"},
    )


def _product(provider: str, product_id: str, title: str) -> Product:
    return Product(
        provider=provider,
        product_id=product_id,
        title=title,
        target="M31",
        ra=10.6847083,
        dec=41.269065,
        wave_range_nm=(100.0, 200.0),
        resolution_R=1000.0,
        wavelength_standard="vacuum",
        flux_units="erg",
        pipeline_version="v1",
        urls={"download": f"https://example.com/{product_id}.fits"},
        citation="Test",
        doi=None,
        extra={},
    )


def test_star_hub_flow(monkeypatch) -> None:
    session = AppSessionState()
    resolver = _resolver()

    hits = [
        ProviderHit(
            provider="MAST",
            product=_product("MAST", "mast-1", "MAST spectrum"),
            telescope="HST",
            instrument="STIS",
            wave_range_nm=(100.0, 200.0),
            preview_url="https://example.com/mast_preview.jpg",
            download_url="https://example.com/mast-1.fits",
        ),
        ProviderHit(
            provider="SDSS",
            product=_product("SDSS", "sdss-2", "SDSS spectrum"),
            telescope="SDSS",
            instrument="BOSS",
            wave_range_nm=(360.0, 950.0),
            preview_url="https://example.com/sdss_preview.jpg",
            download_url="https://example.com/sdss-2.fits",
        ),
    ]

    captured_queries: list[tuple] = []
    ingested_products: list[str] = []

    def fake_resolve(identifier: str, *, use_fixture: bool) -> ResolverResult:  # noqa: FBT002
        assert use_fixture is True
        assert identifier == "M31"
        return resolver

    def fake_provider_names() -> tuple[str, ...]:
        return ("MAST", "SDSS")

    def fake_search_all(query, *, include=None):
        captured_queries.append((query, include))
        return hits

    def fake_ingest(product: Product) -> CanonicalSpectrum:
        ingested_products.append(product.product_id)
        metadata = TraceMetadata(
            provider=product.provider, product_id=product.product_id, title=product.title
        )
        return CanonicalSpectrum(
            label=product.title,
            wavelength_vac_nm=np.array([100.0]),
            values=np.array([1.0]),
            value_mode="flux_density",
            value_unit=product.flux_units,
            metadata=metadata,
            provenance=[],
            source_hash=product.product_id,
        )

    monkeypatch.setattr("app.ui.star_hub.resolver_simbad.resolve", fake_resolve)
    monkeypatch.setattr("app.ui.star_hub.provider_names", fake_provider_names)
    monkeypatch.setattr("app.ui.star_hub.search_all", fake_search_all)
    monkeypatch.setattr("app.ui.star_hub.ingest_product", fake_ingest)

    at = AppTest.from_function(_render_star_hub, args=(session,)).run()

    at.text_input(key="star_hub_query").input("M31").run()
    at.checkbox(key="star_hub_use_fixture").check().run()
    at.button(key="star_hub_resolve").click().run()

    # Trigger provider search.
    at.button(key="star_hub_search").click().run()

    # Select both products and ingest them.
    selection_key = "MAST:mast-1"
    selection_key_two = "SDSS:sdss-2"
    at.multiselect(key="star_hub_selection").select([selection_key, selection_key_two]).run()
    at.button(key="star_hub_add").click().run()

    assert ingested_products == ["mast-1", "sdss-2"]
    assert captured_queries
    query, include = captured_queries[-1]
    assert isinstance(query, ProviderQuery)
    assert include == ["MAST", "SDSS"]
