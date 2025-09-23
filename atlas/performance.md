# Performance Notes

- Plotting uses Plotly WebGL traces (`Scattergl`) for spectra to sustain ~10 traces at 60 fps.
- Line overlays precomputed into flattened coordinate arrays to minimise trace count.
- Ingest dedupe prevents redundant traces, limiting memory bloat.
- Future work: introduce on-demand decimation and asynchronous ingest for large uploads.
