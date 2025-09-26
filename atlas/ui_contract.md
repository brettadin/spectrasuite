# UI Contract Notes

- Tabs: Overlay, Differential, Star Hub, Docs (verified via `get_ui_contract`).
- Sidebar order: Examples → Display Mode → Units → Duplicate Scope → Line Overlays.
- Header: title, version badge (`app_version`), global search field, export button below tabs.
- Overlay tab: file uploader, trace manager checkboxes with axis-family captions and transform provenance
  (unit conversions, air↔vacuum, differential events), Plotly chart with secondary axis for line overlays,
  provenance caption, and similarity analysis controls (viewport, metrics, ribbon, matrices).
- Differential tab: select boxes for trace A/B, buttons for subtraction and ratio with identical
  suppression messaging.
- Star Hub: SIMBAD resolver with fixture toggle, provider fan-out controls (radius, limit, DOI),
  persistent provider/telescope/instrument/λ filters, preview panels, and multi-select "Add to
  overlay" button.
- Docs tab: renders markdown from `docs/static`.
