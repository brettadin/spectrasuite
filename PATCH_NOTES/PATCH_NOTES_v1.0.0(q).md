# Spectra App v1.0.0 (q) — Docs tab refresh

## Highlights
- Restored the in-app Docs tab with recursive Markdown discovery, navigation, and YAML front matter support.
- Added user-facing documentation pages covering the project overview, day-to-day usage, and citation guidance.
- Surfaced per-document summaries and source paths so analysts can audit documentation provenance.

## Changes
- Replaced the minimal docs renderer with a structured loader that parses optional front matter (`title`, `group`, `order`, `summary`).
- Updated `_DOCS_DIR` resolution so deployments correctly read `docs/static/` from the repository root.
- Authored new Markdown pages: refreshed overview, `user_guide.md`, and `citations.md`.
- Created `IMPLEMENTATION_NOTES.md` to track feature context, external references, and validation steps for this iteration.

## Known Issues
- Documentation still renders Markdown only; embedded interactive content (e.g., Plotly snippets) remains out of scope for now.
- Group ordering is driven by front-matter weights; future runs may surface collapsible sections for large doc sets.

## Verification
- `ruff check app/ui/docs.py`
- `black --check app/ui/docs.py`
- `mypy app/ui/docs.py`
- `PYTHONPATH=. pytest -q`
- `python tools/verifiers/Verify-Atlas.py`
- `python tools/verifiers/Verify-PatchNotes.py`
- `python tools/verifiers/Verify-Brains.py`
- `python tools/verifiers/Verify-Handoff.py`
- `PYTHONPATH=. python tools/verifiers/Verify-UI-Contract.py`
