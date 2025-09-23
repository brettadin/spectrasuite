"""Streamlit entry point used by Streamlit CLI."""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_repo_on_path() -> None:
    """Prepend the repository root to ``sys.path`` when executed directly.

    Streamlit executes scripts similarly to ``python app/app_patched.py`` which means
    ``sys.path`` may already contain unrelated ``app`` packages that shadow this
    repository. To guarantee we import the local ``app.ui.main`` module we insert the
    project root ahead of any existing entries.
    """

    repo_root = Path(__file__).resolve().parents[1]
    repo_path = str(repo_root)
    if repo_path not in sys.path:
        sys.path.insert(0, repo_path)


_ensure_repo_on_path()

from app.ui.main import run_app

if __name__ == "__main__":
    run_app()
