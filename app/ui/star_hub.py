"""Star Hub tab combining resolver and provider registry searches."""

from __future__ import annotations

from ast import literal_eval
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import streamlit as st

from app.state.session import AppSessionState
from server.fetchers import resolver_simbad
from server.fetchers.ingest_product import ProductIngestError, ingest_product
from server.fetchers.models import ResolverResult
from server.providers import ProviderHit, ProviderQuery, provider_names, search_all


@dataclass(slots=True)
class _StarHubState:
    resolver: ResolverResult | None = None
    hits: dict[str, ProviderHit] = field(default_factory=dict)
    hit_order: list[str] = field(default_factory=list)
    selection: list[str] = field(default_factory=list)


_STATE_KEY = "star_hub_state"
_FILTER_PROVIDERS_KEY = "star_hub_filter_providers"
_FILTER_TELESCOPES_KEY = "star_hub_filter_telescopes"
_FILTER_INSTRUMENTS_KEY = "star_hub_filter_instruments"
_FILTER_WAVE_KEY = "star_hub_filter_wave"
_SELECTION_KEY = "star_hub_selection"


def _get_state() -> _StarHubState:
    stored = st.session_state.get(_STATE_KEY)
    if isinstance(stored, _StarHubState):
        return stored
    state = _StarHubState()
    st.session_state[_STATE_KEY] = state
    return state


def _hit_key(hit: ProviderHit) -> str:
    product_id = hit.product.product_id or hit.product.title or "unknown"
    return f"{hit.provider}:{product_id}"


def _expand_string_entry(entry: str, hits: dict[str, ProviderHit]) -> list[str]:
    if entry in hits:
        return [entry]
    if entry.startswith("[") and entry.endswith("]"):
        try:
            decoded = literal_eval(entry)
        except (ValueError, SyntaxError):
            return []
        if isinstance(decoded, list):
            return _expand_sequence_entry(decoded, hits)
        return []
    for key, hit in hits.items():
        if _format_hit_label(hit) == entry:
            return [key]
    return []


def _expand_sequence_entry(entry: Sequence[Any], hits: dict[str, ProviderHit]) -> list[str]:
    keys: list[str] = []
    for item in entry:
        keys.extend(_expand_selection_entry(item, hits))
    return keys


def _expand_selection_entry(entry: Any, hits: dict[str, ProviderHit]) -> list[str]:
    if isinstance(entry, str):
        return _expand_string_entry(entry, hits)
    if isinstance(entry, Sequence):
        return _expand_sequence_entry(entry, hits)
    return []


def _format_wave_range(wave_range: tuple[float, float] | None) -> str:
    if not wave_range:
        return "—"
    start, end = wave_range
    return f"{start:.1f}–{end:.1f} nm"


def _format_hit_label(hit: ProviderHit) -> str:
    title = hit.product.title or hit.product.product_id or "Archive product"
    parts = [hit.provider]
    if hit.telescope:
        parts.append(hit.telescope)
    if hit.instrument:
        parts.append(hit.instrument)
    summary = ", ".join(parts)
    return f"{title} ({summary})"


def _store_hits(state: _StarHubState, hits: list[ProviderHit]) -> None:
    mapping = {_hit_key(hit): hit for hit in hits}
    state.hits = mapping
    state.hit_order = list(mapping.keys())
    current_selection = st.session_state.get(_SELECTION_KEY, [])
    filtered_selection = [key for key in current_selection if key in state.hits]
    st.session_state[_SELECTION_KEY] = filtered_selection
    state.selection = filtered_selection


def _hit_metadata_lines(product: ProviderHit) -> list[str]:
    parts = [product.provider]
    if product.telescope:
        parts.append(product.telescope)
    if product.instrument:
        parts.append(product.instrument)
    if product.wave_range_nm:
        parts.append(_format_wave_range(product.wave_range_nm))
    return parts


def _render_hit_details(product: ProviderHit) -> None:
    record = product.product
    if record.target:
        st.write(f"Target: {record.target}")
    if record.pipeline_version:
        st.write(f"Pipeline: {record.pipeline_version}")
    if record.flux_units:
        st.write(f"Flux units: {record.flux_units}")
    portal = record.urls.get("portal")
    if portal:
        st.markdown(f"[Portal link]({portal})")
    if product.download_url:
        st.markdown(f"[Download link]({product.download_url})")
    if record.doi:
        st.write(f"DOI: {record.doi}")
    if product.extras:
        with st.expander("More details", expanded=False):
            st.json(product.extras)


def _render_hit_preview(hit: ProviderHit) -> None:
    if not hit.preview_url:
        return
    try:
        st.image(hit.preview_url, caption="Preview", use_column_width=True)
    except Exception:
        st.markdown(f"[Preview image]({hit.preview_url})")


def _render_hit_card(hit: ProviderHit) -> None:
    record = hit.product
    title = record.title or record.product_id or "Archive product"
    with st.container():
        st.markdown(f"**{title}**")
        st.caption(" | ".join(_hit_metadata_lines(hit)))
        details_col, preview_col = st.columns([3, 2])
        with details_col:
            _render_hit_details(hit)
        with preview_col:
            _render_hit_preview(hit)


def _sync_options(key: str, options: list[str]) -> None:
    stored = st.session_state.get(key)
    if not isinstance(stored, list):
        st.session_state[key] = list(options)
        return
    filtered = [option for option in stored if option in options]
    for option in options:
        if option not in filtered:
            filtered.append(option)
    st.session_state[key] = filtered


def _configure_filters(hits: list[ProviderHit]) -> tuple[list[str], list[str], list[str]]:
    provider_options = sorted({hit.provider for hit in hits})
    telescope_options = sorted({hit.telescope for hit in hits if hit.telescope})
    instrument_options = sorted({hit.instrument for hit in hits if hit.instrument})
    _sync_options(_FILTER_PROVIDERS_KEY, provider_options)
    _sync_options(_FILTER_TELESCOPES_KEY, telescope_options)
    _sync_options(_FILTER_INSTRUMENTS_KEY, instrument_options)
    return provider_options, telescope_options, instrument_options


def _select_wave_window(hits: list[ProviderHit]) -> list[ProviderHit]:
    wave_ranges = [hit.wave_range_nm for hit in hits if hit.wave_range_nm]
    if not wave_ranges:
        st.session_state.pop(_FILTER_WAVE_KEY, None)
        return hits

    min_wave = min(start for start, _ in wave_ranges)
    max_wave = max(end for _, end in wave_ranges)
    if _FILTER_WAVE_KEY not in st.session_state:
        st.session_state[_FILTER_WAVE_KEY] = (float(min_wave), float(max_wave))
    start_sel, end_sel = st.slider(
        "Wavelength range (nm)",
        min_value=float(min_wave),
        max_value=float(max_wave),
        value=st.session_state[_FILTER_WAVE_KEY],
        key=_FILTER_WAVE_KEY,
    )

    def _within_wave(hit: ProviderHit) -> bool:
        if not hit.wave_range_nm:
            return True
        start, end = hit.wave_range_nm
        return end >= start_sel and start <= end_sel

    return [hit for hit in hits if _within_wave(hit)]


def _filtered_hits(state: _StarHubState) -> list[ProviderHit]:
    hits = [state.hits[key] for key in state.hit_order if key in state.hits]
    if not hits:
        return []

    provider_options, telescope_options, instrument_options = _configure_filters(hits)

    selected_providers = st.multiselect(
        "Providers",
        provider_options,
        default=st.session_state[_FILTER_PROVIDERS_KEY],
        key=_FILTER_PROVIDERS_KEY,
        help="Filter results by provider.",
    )
    selected_telescopes = st.multiselect(
        "Telescopes",
        telescope_options,
        default=st.session_state[_FILTER_TELESCOPES_KEY],
        key=_FILTER_TELESCOPES_KEY,
        help="Filter results by telescope when available.",
    )
    selected_instruments = st.multiselect(
        "Instruments",
        instrument_options,
        default=st.session_state[_FILTER_INSTRUMENTS_KEY],
        key=_FILTER_INSTRUMENTS_KEY,
        help="Filter results by instrument when available.",
    )

    candidates = _select_wave_window(hits)
    filtered: list[ProviderHit] = []
    for hit in candidates:
        if selected_providers and hit.provider not in selected_providers:
            continue
        if selected_telescopes and hit.telescope not in selected_telescopes:
            continue
        if selected_instruments and hit.instrument not in selected_instruments:
            continue
        filtered.append(hit)
    return filtered


def _run_search(state: _StarHubState, identifier: str) -> None:
    if state.resolver is None:
        st.warning("Resolve a target before searching providers.")
        return

    provider_choices = provider_names()
    default_selection = list(provider_choices)
    selected_providers = st.multiselect(
        "Providers to query",
        provider_choices,
        default=default_selection,
        key="star_hub_providers_to_query",
        help="Choose which providers to query.",
    )

    radius = st.slider(
        "Search radius (arcsec)",
        min_value=1.0,
        max_value=120.0,
        value=10.0,
        step=1.0,
        key="star_hub_radius",
    )
    limit = st.slider(
        "Result limit",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        key="star_hub_limit",
    )
    sdss_class = st.selectbox(
        "SDSS spectral class",
        options=["(any)", "STAR", "GALAXY", "QSO"],
        index=0,
        key="star_hub_sdss_class",
        help="Limit SDSS results to a class when available.",
    )
    doi_filter = st.text_input(
        "DOI filter",
        value="",
        key="star_hub_doi_filter",
        help="Query DOI provider when a DOI is known.",
    ).strip()

    if st.button("Search providers", key="star_hub_search"):
        filters: dict[str, Any] = {
            "mast_radius_arcsec": radius,
            "sdss_radius_arcsec": radius,
            "sdss_limit": limit,
        }
        if sdss_class != "(any)":
            filters["sdss_class"] = sdss_class
        if doi_filter:
            filters["doi"] = doi_filter
        query = ProviderQuery(
            identifier=identifier,
            resolver=state.resolver,
            radius_arcsec=radius,
            limit=limit,
            filters=filters,
        )
        with st.spinner("Searching providers..."):
            hits = search_all(query, include=selected_providers or None)
        _store_hits(state, hits)
        if hits:
            st.success(f"Found {len(hits)} product(s) across providers.")
        else:
            st.info("No matching products found for the current parameters.")


def _ingest_selected(
    session: AppSessionState, state: _StarHubState, selection: list[str] | None = None
) -> None:
    if selection is None:
        raw_selection = state.selection
    else:
        raw_selection = selection
    selected: list[str] = []
    seen: set[str] = set()
    for entry in raw_selection:
        for key in _expand_selection_entry(entry, state.hits):
            if key not in seen and key in state.hits:
                seen.add(key)
                selected.append(key)
    if not selected:
        st.warning("Select one or more products before adding to the overlay.")
        return

    hits = [state.hits[key] for key in selected]
    with st.spinner("Downloading and ingesting selected products..."):
        results: list[str] = []
        for hit in hits:
            try:
                canonical = ingest_product(hit.product)
            except ProductIngestError as exc:
                st.error(str(exc))
                continue
            added, trace_id = session.register_trace(canonical)
            label = canonical.label
            if added:
                results.append(f"✅ Added '{label}'")
            else:
                results.append(f"⚠️ Duplicate for '{label}' (trace {trace_id})")
        if results:
            st.write("\n".join(results))
    st.session_state[_SELECTION_KEY] = []


def render_star_hub_tab(session: "AppSessionState") -> None:  # noqa: UP037, C901
    st.subheader("Star Hub")
    state = _get_state()

    query = st.text_input("Resolve target (SIMBAD)", key="star_hub_query")
    use_fixture = st.checkbox("Use fixture", key="star_hub_use_fixture")
    if st.button("Resolve", key="star_hub_resolve"):
        if not query.strip():
            st.error("Enter a target name or coordinates")
        else:
            with st.spinner("Resolving target..."):
                try:
                    result = resolver_simbad.resolve(query, use_fixture=use_fixture)
                except Exception as exc:  # pragma: no cover - network path
                    st.error(f"Resolver error: {exc}")
                else:
                    state.resolver = result
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
        _run_search(state, query)
    else:
        st.info("Use the resolver above to seed archive searches.")
        return

    if state.hits:
        st.divider()
        st.markdown("### Provider results")
        filtered = _filtered_hits(state)
        option_keys = [_hit_key(hit) for hit in filtered]
        options_map = {_hit_key(hit): hit for hit in filtered}
        current_selection = [
            key for key in st.session_state.get(_SELECTION_KEY, []) if key in options_map
        ]

        selection = st.multiselect(
            "Select products to add to the overlay",
            options=option_keys,
            default=current_selection,
            key=_SELECTION_KEY,
            help="Choose product keys to ingest; details appear below.",
        )
        state.selection = list(selection)
        for hit in filtered:
            _render_hit_card(hit)
        if st.button("Add selected to overlay", key="star_hub_add"):
            _ingest_selected(session, state, selection)
    else:
        st.info("Run a provider search to view available products.")
