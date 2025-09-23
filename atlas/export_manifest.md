# Export & Replay

- `export_session` builds manifest dict (`schema_version`, `app_version`, `axis`, `display_mode`,
  `traces`, `overlay`). Visible traces written as CSVs on the selected wavelength unit; manifest
  stores canonical arrays for replay.
- PNG export uses Plotly/Kaleido when available (empty placeholder if Kaleido missing).
- Manifest replay: `replay_manifest` reconstructs `CanonicalSpectrum` instances from stored data.
- Export button writes bundle to `st.session_state['export_bytes']` for download.
- Future: CLI replay script will consume manifest to rebuild Streamlit state.
