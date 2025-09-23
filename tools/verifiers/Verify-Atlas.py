#!/usr/bin/env python3
"""Ensure atlas documentation set is present and non-empty."""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED = [
    "atlas/README.md",
    "atlas/architecture.md",
    "atlas/ui_contract.md",
    "atlas/data_model.md",
    "atlas/ingest_ascii.md",
    "atlas/transforms.md",
    "atlas/export_manifest.md",
    "atlas/fetchers_overview.md",
    "atlas/overlays_lines.md",
    "atlas/performance.md",
    "atlas/testing.md",
]


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    missing: list[str] = []
    empty: list[str] = []
    for rel in REQUIRED:
        path = root / rel
        if not path.exists():
            missing.append(rel)
            continue
        if not path.read_text(encoding="utf-8").strip():
            empty.append(rel)
    if missing or empty:
        if missing:
            print("Missing atlas files:", ", ".join(missing))
        if empty:
            print("Empty atlas files:", ", ".join(empty))
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - invoked via CLI
    sys.exit(main())
