from __future__ import annotations

from server.fetchers import doi
from server.fetchers.eso import search as eso_search
from server.fetchers.models import Product, ResolverResult
from server.providers import (
    ProviderHit,
    ProviderQuery,
    register_provider,
    search_all,
    unregister_provider,
)


def _resolver() -> ResolverResult:
    return ResolverResult(
        canonical_name="M31",
        ra=10.6847083,
        dec=41.269065,
        object_type="GALAXY",
        aliases=["Andromeda"],
        provenance={"source": "test"},
    )


def test_eso_provider_filters() -> None:
    query = ProviderQuery(identifier="M31", resolver=_resolver(), radius_arcsec=30.0)
    hits = list(eso_search(query))
    assert len(hits) == 2

    filtered_query = ProviderQuery(
        identifier="M31",
        resolver=_resolver(),
        radius_arcsec=30.0,
        filters={"eso_instrument": "UVES"},
    )
    filtered_hits = list(eso_search(filtered_query))
    assert len(filtered_hits) == 1
    assert filtered_hits[0].instrument == "UVES"


def test_doi_provider_matches_filter() -> None:
    query = ProviderQuery(identifier="M31", resolver=_resolver(), filters={})
    assert list(doi.search(query)) == []

    doi_query = ProviderQuery(
        identifier="10.17909/T9XX11",
        resolver=_resolver(),
        filters={"doi": "10.17909/T9XX11"},
    )
    hits = list(doi.search(doi_query))
    assert len(hits) == 1
    hit = hits[0]
    assert hit.provider == "DOI"
    assert hit.product.provider == "MAST"


def test_registry_deduplicates_hits() -> None:
    product = Product(
        provider="TEST-ARCHIVE",
        product_id="shared",
        title="Shared spectrum",
        target="Target",
        ra=1.0,
        dec=1.0,
        wave_range_nm=(400.0, 500.0),
        resolution_R=1000.0,
        wavelength_standard="vacuum",
        flux_units="unit",
        pipeline_version="v1",
        urls={"download": "https://example.com/shared.fits"},
        citation="Test",
        doi=None,
        extra={},
    )

    def provider_one(_: ProviderQuery):
        return [ProviderHit(provider="ONE", product=product)]

    def provider_two(_: ProviderQuery):
        return [ProviderHit(provider="TWO", product=product)]

    register_provider("TEST_ONE", provider_one)
    register_provider("TEST_TWO", provider_two)

    try:
        query = ProviderQuery(identifier="target", resolver=_resolver())
        hits = search_all(query, include=["TEST_ONE", "TEST_TWO"])
        assert len(hits) == 1
        assert hits[0].product.product_id == "shared"
    finally:
        unregister_provider("TEST_ONE")
        unregister_provider("TEST_TWO")
