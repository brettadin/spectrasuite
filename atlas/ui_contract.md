# UI Contract Notes

- Tabs: Overlay, Differential, Star Hub, Docs (verified via `get_ui_contract`).
- Sidebar order: Examples → Display Mode → Units → Duplicate Scope → Line Overlays.
- Header: title, version badge (`app_version`), global search field, export button below tabs.
- Overlay tab: file uploader, trace manager checkboxes with axis-family captions, Plotly chart with
  secondary axis for line overlays, provenance caption.
- Differential tab: select boxes for trace A/B, buttons for subtraction and ratio with identical
  suppression messaging.
- Star Hub: SIMBAD resolver card placeholder; future runs expand provider grid.
- Docs tab: renders markdown from `docs/static`.
