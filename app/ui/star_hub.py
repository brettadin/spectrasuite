"""Star Hub tab with resolver and archive integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import streamlit as st

from app.state.session import AppSessionState
from server.fetchers import mast, resolver_simbad, sdss
from server.fetchers.ingest_product import ProductIngestError, ingest_product
from server.fetchers.models import Product, ResolverResult


@dataclass(slots=True)
class _StarHubState:
    resolver: ResolverResult | None = None
    mast_products: list[Product] = field(default_factory=list)
    sdss_products: list[Product] = field(default_factory=list)
    sdss_search_results: list[Product] = field(default_factory=list)


_STATE_KEY = "star_hub_state"


def _get_state() -> _StarHubState:
    stored = st.session_state.get(_STATE_KEY)
    if isinstance(stored, _StarHubState):
        return stored
    state = _StarHubState()
    st.session_state[_STATE_KEY] = state
    return state


def _format_wave_range(wave_range: tuple[float, float] | None) -> str:
    if not wave_range:
        return "—"
    start, end = wave_range
    return f"{start:.1f}–{end:.1f} nm"


def _render_product_card(session: AppSessionState, product: Product, *, key_prefix: str) -> None:
    with st.container():
        title = product.title or product.product_id or "Archive product"
        st.markdown(f"**{title}**")
        st.caption(
            " | ".join(
                filter(
                    None,
                    [
                        product.provider,
                        f"λ: {_format_wave_range(product.wave_range_nm)}",
                        (
                            f"R ≈ {product.resolution_R:.0f}"
                            if product.resolution_R is not None
                            else None
                        ),
                    ],
                )
            )
        )
        cols = st.columns([3, 1])
        with cols[0]:
            if product.target:
                st.write(f"Target: {product.target}")
            if product.pipeline_version:
                st.write(f"Pipeline: {product.pipeline_version}")
            if product.flux_units:
                st.write(f"Flux units: {product.flux_units}")
            if product.urls.get("portal"):
                st.markdown(
                    f"[Portal link]({product.urls['portal']})", help="Open the archive summary"
                )
            download_url = product.urls.get("download")
            product_url = product.urls.get("product")
            if download_url:
                st.markdown(
                    f"[Download link]({download_url})",
                    help="Direct archive download",
                )
            elif product_url:
                st.markdown(
                    f"[Archive product page (may require archive landing page)]({product_url})",
                    help=(
                        "Opens the archive product page; it may redirect to a "
                        "landing page before the download starts."
                    ),
                )
        with cols[1]:
            if st.button("Add to overlay", key=f"{key_prefix}_add"):
                _ingest_product(session, product)


def _ingest_product(session: AppSessionState, product: Product) -> None:
    with st.spinner("Downloading and ingesting product..."):
        try:
            canonical = ingest_product(product)
        except ProductIngestError as exc:
            st.error(str(exc))
            return
    added, trace_id = session.register_trace(canonical)
    if added:
        st.success(f"Added trace '{canonical.label}'")
    else:
        st.warning(f"Duplicate detected for '{canonical.label}' (trace {trace_id})")


def _render_mast_section(session: AppSessionState, state: _StarHubState) -> None:
    st.markdown("### MAST archive")
    resolver = state.resolver
    if resolver is None or resolver.ra is None or resolver.dec is None:
        st.info("Resolve a target with coordinates to search MAST products.")
        return

    radius = st.slider(
        "Search radius (arcsec)",
        min_value=1.0,
        max_value=30.0,
        value=5.0,
        step=1.0,
        key="star_hub_mast_radius",
    )

    if st.button("Search MAST", key="star_hub_mast_search"):
        with st.spinner("Querying MAST..."):
            try:
                products = list(
                    mast.search_products(ra=resolver.ra, dec=resolver.dec, radius_arcsec=radius)
                )
            except RuntimeError as exc:
                st.error(str(exc))
            else:
                state.mast_products = list(products)
                if not products:
                    st.info("No spectroscopic products found for the selected radius.")

    if state.mast_products:
        st.write(f"Found {len(state.mast_products)} spectroscopic product(s).")
        for index, product in enumerate(state.mast_products):
            _render_product_card(session, product, key_prefix=f"mast_{index}")


def _sdss_specobj_controls(state: _StarHubState) -> None:
    specobj_input = st.text_input("SpecObjID", key="star_hub_sdss_specobj")
    if not st.button("Fetch by SpecObjID", key="star_hub_sdss_fetch_specobj"):
        return
    cleaned = specobj_input.strip()
    if not cleaned:
        st.error("Enter a SpecObjID to query SDSS.")
        return
    try:
        specobjid = int(cleaned)
    except ValueError:
        st.error("SpecObjID must be an integer")
        return
    with st.spinner("Fetching SDSS spectrum..."):
        try:
            product = sdss.fetch_by_specobjid(specobjid)
        except Exception as exc:  # pragma: no cover - network path
            st.error(str(exc))
            return
    _store_sdss_product(state, product)


def _sdss_plate_controls(state: _StarHubState) -> None:
    plate_col, mjd_col, fiber_col = st.columns(3)
    plate_input = plate_col.text_input("Plate", key="star_hub_sdss_plate")
    mjd_input = mjd_col.text_input("MJD", key="star_hub_sdss_mjd")
    fiber_input = fiber_col.text_input("Fiber", key="star_hub_sdss_fiber")
    if not st.button("Fetch by plate/MJD/fiber", key="star_hub_sdss_fetch_plate"):
        return
    try:
        plate = int(plate_input.strip())
        mjd = int(mjd_input.strip())
        fiber = int(fiber_input.strip())
    except ValueError:
        st.error("Plate, MJD, and Fiber must be integers")
        return
    with st.spinner("Fetching SDSS spectrum..."):
        try:
            product = sdss.fetch_by_plate(plate=plate, mjd=mjd, fiber=fiber)
        except Exception as exc:  # pragma: no cover - network path
            st.error(str(exc))
            return
    _store_sdss_product(state, product)


def _render_sdss_search_section(session: AppSessionState, state: _StarHubState) -> None:
    st.markdown("#### Search SDSS by resolved position")
    resolver = state.resolver
    if resolver is None or resolver.ra is None or resolver.dec is None:
        st.info("Resolve a target with coordinates to search nearby SDSS spectra.")
        return

    radius = st.slider(
        "Search radius (arcsec)",
        min_value=1.0,
        max_value=180.0,
        value=30.0,
        step=1.0,
        key="star_hub_sdss_radius",
    )
    class_options = ["(any)", "STAR", "GALAXY", "QSO"]
    selected_class = st.selectbox(
        "Spectral class",
        options=class_options,
        index=0,
        key="star_hub_sdss_class",
        help="Filter SDSS results by the archive classification when available.",
    )
    limit = st.slider(
        "Result limit",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        key="star_hub_sdss_limit",
    )

    if st.button("Search SDSS region", key="star_hub_sdss_search"):
        filter_kwargs: dict[str, Any] = {}
        if selected_class != "(any)":
            filter_kwargs["class_"] = selected_class
        with st.spinner("Querying SDSS..."):
            try:
                products = list(
                    sdss.search_spectra(
                        ra=resolver.ra,
                        dec=resolver.dec,
                        radius_arcsec=radius,
                        limit=limit,
                        **filter_kwargs,
                    )
                )
            except Exception as exc:  # pragma: no cover - network path
                st.error(str(exc))
            else:
                state.sdss_search_results = products
                if not products:
                    st.info("No SDSS spectra found for the selected parameters.")

    if state.sdss_search_results:
        st.write(f"Found {len(state.sdss_search_results)} SDSS spectrum(s).")
        for index, product in enumerate(state.sdss_search_results):
            _render_product_card(session, product, key_prefix=f"sdss_search_{index}")


def _render_sdss_section(session: AppSessionState, state: _StarHubState) -> None:
    st.markdown("### SDSS archive")
    _sdss_specobj_controls(state)
    st.caption("Or fetch by plate / MJD / fiber identifiers")
    _sdss_plate_controls(state)

    _render_sdss_search_section(session, state)

    if state.sdss_products:
        st.write(f"Stored {len(state.sdss_products)} SDSS spectrum(s).")
        for index, product in enumerate(state.sdss_products):
            _render_product_card(session, product, key_prefix=f"sdss_{index}")


def _store_sdss_product(state: _StarHubState, product: Product) -> None:
    existing_ids = {item.product_id for item in state.sdss_products}
    if product.product_id in existing_ids:
        return
    state.sdss_products.append(product)


def render_star_hub_tab(session: AppSessionState) -> None:
    st.subheader("Star Hub")
    state = _get_state()

    query = st.text_input("Resolve target (SIMBAD)", key="star_hub_query")
    if st.button("Resolve", key="star_hub_resolve"):
        if not query.strip():
            st.error("Enter a target name or coordinates")
        else:
            with st.spinner("Resolving target..."):
                try:
                    result = resolver_simbad.resolve(query)
                except Exception as exc:  # pragma: no cover - network path
                    st.error(f"Resolver error: {exc}")
                else:
                    state.resolver = result
                    state.mast_products.clear()
                    st.success(f"Resolved {result.canonical_name}")

    if state.resolver:
        resolver = state.resolver
        st.json(
            {
                "name": resolver.canonical_name,
                "ra_deg": resolver.ra,
                "dec_deg": resolver.dec,
                "object_type": resolver.object_type,
                "aliases": resolver.aliases,
                "provenance": resolver.provenance,
            }
        )
        _render_mast_section(session, state)
    else:
        st.info("Use the resolver above to seed archive searches.")

    st.divider()
    _render_sdss_section(session, state)
