"""Docs tab renderer."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st
import yaml  # type: ignore[import-untyped]

_DOCS_DIR = Path(__file__).resolve().parents[3] / "docs" / "static"


@dataclass(frozen=True)
class DocEntry:
    """Renderable documentation entry."""

    path: Path
    title: str
    group: str | None
    order: int
    summary: str | None
    body: str

    @property
    def label(self) -> str:
        if self.group:
            return f"{self.group} · {self.title}"
        return self.title


def _iter_markdown_files() -> Iterator[Path]:
    if not _DOCS_DIR.exists():
        return iter(())
    files = [path for path in sorted(_DOCS_DIR.rglob("*.md")) if path.is_file()]
    return iter(files)


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            raw_meta = "\n".join(lines[1:index])
            body = "\n".join(lines[index + 1 :]).lstrip("\n")
            metadata = _safe_load_yaml(raw_meta)
            return metadata, body

    return {}, text


def _safe_load_yaml(payload: str) -> dict[str, Any]:
    if not payload.strip():
        return {}
    try:
        loaded = yaml.safe_load(payload) or {}
    except yaml.YAMLError:
        return {}
    if not isinstance(loaded, dict):
        return {}
    return loaded


def _load_docs() -> list[DocEntry]:
    entries: list[DocEntry] = []
    for path in _iter_markdown_files():
        text = path.read_text(encoding="utf-8")
        metadata, body = _parse_front_matter(text)
        title = (metadata.get("title") or path.stem).replace("_", " ").title()
        group = metadata.get("group") or metadata.get("category")
        order = _coerce_int(
            metadata.get("order") or metadata.get("weight") or metadata.get("priority") or 0
        )
        summary = metadata.get("summary") or metadata.get("description")
        entries.append(
            DocEntry(
                path=path,
                title=title,
                group=group,
                order=order,
                summary=summary if isinstance(summary, str) else None,
                body=body or "(This document has no content yet.)",
            )
        )

    entries.sort(key=lambda entry: (entry.group or "", entry.order, entry.title.lower()))
    return entries


def render_docs_tab() -> None:
    st.header("Documentation")

    entries = _load_docs()
    if not entries:
        st.info(
            "Documentation is not available. Add Markdown files to `docs/static/` to populate this tab."
        )
        return

    nav_col, content_col = st.columns([1, 3])

    with nav_col:
        st.subheader("Contents")
        options = list(range(len(entries)))
        selected_index = st.radio(
            "Select a document",
            options,
            index=0,
            format_func=lambda idx: entries[idx].label,
            label_visibility="collapsed",
        )
        selected_entry = entries[selected_index]
        if selected_entry.summary:
            st.caption(selected_entry.summary)

    with content_col:
        st.subheader(selected_entry.title)
        st.markdown(selected_entry.body)
        relative_path = selected_entry.path.relative_to(_DOCS_DIR)
        st.caption(f"Source: `{relative_path}`")
