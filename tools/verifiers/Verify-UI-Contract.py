#!/usr/bin/env python3
"""Headless UI contract verification."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.ui.main import get_ui_contract

EXPECTED_TABS = ["Overlay", "Differential", "Star Hub", "Docs"]
EXPECTED_SIDEBAR = ["Examples", "Display Mode", "Units", "Duplicate Scope", "Line Overlays"]


def main() -> int:
    contract = get_ui_contract()
    if contract.tabs != EXPECTED_TABS:
        print(f"Tab contract mismatch: {contract.tabs} != {EXPECTED_TABS}")
        return 1
    if contract.sidebar_sections != EXPECTED_SIDEBAR:
        print("Sidebar contract mismatch")
        return 1
    version_path = Path(__file__).resolve().parents[2] / "app" / "config" / "version.json"
    payload = json.loads(version_path.read_text())
    if not payload.get("app_version"):
        print("Version badge missing app_version")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
