#!/usr/bin/env python3
"""Validate that a handoff file exists for the current run."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HEADINGS = [
    "## 1) Summary of This Run",
    "## 2) Current State of the Project",
    "## 3) Next Steps (Prioritized)",
    "## 4) Decisions & Rationale",
    "## 5) References",
    "## 6) Quick Start for the Next AI",
]

VERSION_PATTERN = re.compile(r"^(?P<base>\d+\.\d+\.\d+)(?P<letter>[a-z])$")


def _current_version(root: Path) -> tuple[str, str]:
    payload = json.loads((root / "app" / "config" / "version.json").read_text())
    match = VERSION_PATTERN.match(payload["app_version"])
    if not match:
        raise ValueError("app_version not in expected format")
    return match.group("base"), match.group("letter")


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    template = root / "handoffs" / "HANDOFF_TEMPLATE.md"
    if not template.exists():
        print("Handoff template missing")
        return 1

    base, letter = _current_version(root)
    target = root / "handoffs" / f"HANDOFF_v{base}({letter}).md"
    if not target.exists():
        print(f"Handoff file missing: {target.name}")
        return 1

    text = target.read_text(encoding="utf-8")
    missing = [heading for heading in HEADINGS if heading not in text]
    if missing:
        print(f"Handoff missing headings: {', '.join(missing)}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
