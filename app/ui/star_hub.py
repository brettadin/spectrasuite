"""Star Hub tab stub with SIMBAD resolver integration."""

from __future__ import annotations

import streamlit as st

from app.state.session import AppSessionState
from server.fetchers import resolver_simbad


def render_star_hub_tab(session: AppSessionState) -> None:  # noqa: ARG001
    st.subheader("Star Hub")
    query = st.text_input("Resolve target (SIMBAD)", key="star_hub_query")
    if st.button("Resolve", key="star_hub_resolve"):
        if not query.strip():
            st.error("Enter a target name or coordinates")
        else:
            try:
                result = resolver_simbad.resolve(query)
            except Exception as exc:  # pragma: no cover - network path
                st.error(f"Resolver error: {exc}")
            else:
                st.success(f"Resolved {result.canonical_name}")
                st.json(
                    {
                        "name": result.canonical_name,
                        "ra_deg": result.ra,
                        "dec_deg": result.dec,
                        "object_type": result.object_type,
                        "aliases": result.aliases,
                        "provenance": result.provenance,
                    }
                )
                st.info("Archive product search will land here in a future run.")
