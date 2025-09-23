"""Docs tab renderer."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import streamlit as st

_DOCS_DIR = Path(__file__).resolve().parents[2] / "docs" / "static"


def _load_docs() -> Iterable[Path]:
    return sorted(path for path in _DOCS_DIR.glob("*.md"))


def render_docs_tab() -> None:
    st.header("Documentation")
    for path in _load_docs():
        st.subheader(path.stem.replace("_", " ").title())
        st.markdown(path.read_text(encoding="utf-8"))
