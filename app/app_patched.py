"""Streamlit entry point used by the Streamlit CLI."""

from __future__ import annotations

import sys
from collections.abc import Callable
from importlib import import_module
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


def _load_run_app() -> Callable[[], None]:
    """Import and return ``app.ui.main.run_app`` after fixing ``sys.path``."""
    _ensure_repo_on_path()
    module = import_module("app.ui.main")
    return module.run_app


run_app = _load_run_app()


def main() -> None:
    run_app()


if __name__ == "__main__":
    main()
