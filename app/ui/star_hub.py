"""Star Hub tab with resolver and archive integration."""

from __future__ import annotations

from dataclasses import dataclass, field

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


_SDSS_SURVEY_OPTIONS: list[tuple[str, str | None]] = [
    ("Any survey", None),
    ("Legacy (SDSS)", "sdss"),
    ("BOSS", "boss"),
    ("APOGEE-1", "apogee1"),
    ("APOGEE-2", "apogee2"),
]

_SDSS_INSTRUMENT_OPTIONS: list[tuple[str, str | None]] = [
    ("Any instrument", None),
    ("SDSS optical", "SDSS"),
    ("BOSS optical", "BOSS"),
    ("APOGEE (near-IR)", "APOGEE"),
]

_SDSS_CLASS_OPTIONS: list[tuple[str, str | None]] = [
    ("Any object class", None),
    ("Stellar (STAR)", "STAR"),
    ("Galaxy (GALAXY)", "GALAXY"),
    ("Quasar (QSO)", "QSO"),
]


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


def _parse_optional_float(value: str) -> float | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    return float(cleaned)


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
            if product.urls.get("download"):
                st.markdown(
                    f"[Download link]({product.urls['download']})",
                    help="Direct archive download",
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


def _render_sdss_filters(state: _StarHubState) -> None:
    st.caption("Search SDSS by survey, telescope, and class filters")

    survey_labels = [label for label, _ in _SDSS_SURVEY_OPTIONS]
    instrument_labels = [label for label, _ in _SDSS_INSTRUMENT_OPTIONS]
    class_labels = [label for label, _ in _SDSS_CLASS_OPTIONS]

    survey_choice = st.selectbox(
        "Survey",
        options=survey_labels,
        index=0,
        key="star_hub_sdss_survey",
        help="Restrict results to a specific SDSS survey",
    )
    instrument_choice = st.selectbox(
        "Instrument",
        options=instrument_labels,
        index=0,
        key="star_hub_sdss_instrument",
        help="Limit by spectrograph",
    )
    class_choice = st.selectbox(
        "Object class",
        options=class_labels,
        index=1,
        key="star_hub_sdss_class",
        help="Prioritize stellar targets or broaden the search",
    )

    wave_cols = st.columns(2)
    wave_min_input = wave_cols[0].text_input(
        "Min wavelength (nm)",
        key="star_hub_sdss_wave_min",
        placeholder="Optional",
        help="Lower wavelength bound for the metadata query",
    )
    wave_max_input = wave_cols[1].text_input(
        "Max wavelength (nm)",
        key="star_hub_sdss_wave_max",
        placeholder="Optional",
        help="Upper wavelength bound for the metadata query",
    )

    if not st.button("Search SDSS metadata", key="star_hub_sdss_search"):
        return

    try:
        wave_min = _parse_optional_float(wave_min_input)
    except ValueError:
        st.error("Minimum wavelength must be numeric if provided")
        return
    try:
        wave_max = _parse_optional_float(wave_max_input)
    except ValueError:
        st.error("Maximum wavelength must be numeric if provided")
        return

    survey_value = dict(_SDSS_SURVEY_OPTIONS)[survey_choice]
    instrument_value = dict(_SDSS_INSTRUMENT_OPTIONS)[instrument_choice]
    class_value = dict(_SDSS_CLASS_OPTIONS)[class_choice]

    with st.spinner("Querying SDSS metadata..."):
        try:
            products = sdss.search_spectra(
                survey=survey_value,
                instrument=instrument_value,
                class_name=class_value,
                wave_min_nm=wave_min,
                wave_max_nm=wave_max,
            )
        except LookupError:
            state.sdss_search_results.clear()
            st.info("No spectra matched the selected filters.")
            return
        except Exception as exc:  # pragma: no cover - network path
            st.error(str(exc))
            return

    state.sdss_search_results = list(products)
    if not state.sdss_search_results:
        st.info("No spectra matched the selected filters.")


def _render_sdss_search_result(state: _StarHubState, product: Product, index: int) -> None:
    with st.container():
        st.markdown(f"**{product.title}**")
        survey = product.extra.get("survey")
        instrument = product.extra.get("instrument")
        redshift = product.extra.get("z")
        caption_bits = [bit for bit in [survey, instrument, product.target] if bit]
        if redshift is not None:
            caption_bits.append(f"z = {redshift:.4f}")
        if caption_bits:
            st.caption(" | ".join(caption_bits))

        cols = st.columns([3, 1])
        with cols[0]:
            plate = product.extra.get("plate")
            mjd = product.extra.get("mjd")
            fiber = product.extra.get("fiberid")
            if plate and mjd and fiber:
                st.write(f"Plate {plate} • MJD {mjd} • Fiber {fiber}")
            if product.urls.get("portal"):
                st.markdown(
                    f"[SkyServer summary]({product.urls['portal']})",
                    help="Open SDSS SkyServer details",
                )
        with cols[1]:
            if st.button("Fetch spectrum", key=f"sdss_candidate_{index}"):
                try:
                    specobjid = int(product.product_id)
                except (TypeError, ValueError):
                    st.error("SpecObjID unavailable for this result")
                    return
                with st.spinner("Retrieving SDSS spectrum..."):
                    try:
                        fetched = sdss.fetch_by_specobjid(specobjid)
                    except Exception as exc:  # pragma: no cover - network path
                        st.error(str(exc))
                        return
                _store_sdss_product(state, fetched)
                st.success(f"Fetched spectrum {product.product_id}")


def _render_sdss_section(session: AppSessionState, state: _StarHubState) -> None:
    st.markdown("### SDSS archive")
    _render_sdss_filters(state)
    _sdss_specobj_controls(state)
    st.caption("Or fetch by plate / MJD / fiber identifiers")
    _sdss_plate_controls(state)

    if state.sdss_search_results:
        st.write(f"Found {len(state.sdss_search_results)} candidate spectrum(s).")
        for index, product in enumerate(state.sdss_search_results):
            _render_sdss_search_result(state, product, index)

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
