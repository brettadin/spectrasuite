---
title: "User Guide"
group: "Guides"
order: 10
summary: "Step-by-step walkthrough for loading spectra, comparing datasets, and exporting results."
---

# User Guide

## 1. Launch the App

1. Install dependencies: `python -m pip install -e .` from the repository root.
2. Start the development server: `streamlit run app/ui/main.py`.
3. The browser loads the Streamlit interface with tabs for Overlay, Differential, Star Hub, Similarity, and Docs.

## 2. Ingest Spectra

1. Open the **Overlay** tab and use *Upload spectra* to add ASCII (`.txt`, `.csv`) or FITS files.
2. The ingestion pipeline auto-detects wavelength/flux columns, converts air→vacuum when needed, and scales fluxes to SI units using `astropy`/`specutils` conversions.
3. Use the trace manager to review provenance (detected units, conversion history, differential operations).
4. Multi-extension FITS files prompt you to choose an HDU; headerless ASCII files are parsed by heuristics that infer the axis families.

## 3. Overlay & Compare

1. Uploaded traces appear in the overlay plot. Toggle visibility, adjust colours, or set dual Y-axes for disparate flux scales.
2. Enable *Downsample* if a dataset is extremely dense to improve interactivity.
3. Use the **Differential** tab to compute `A - B` or `A / B` products. Outputs inherit provenance metadata so they can be exported or re-analysed.
4. Activate reference line overlays (Fe I from the NIST ASD) to highlight transitions near points of interest.

## 4. Star Hub Archives

1. Visit the **Star Hub** tab and search by target name, coordinate, or identifier.
2. The resolver fans the query out to registered providers (MAST, SDSS, ESO, DOI). Preview cards display context and quality flags.
3. Select one or more products and ingest them directly into the overlay with *Add to session*.
4. Provider warnings or errors surface inline so you can retry or adjust filters.

## 5. Similarity Analysis

1. Navigate to the **Similarity** tab to compute metrics between visible traces (cosine, RMSE, correlation, line-match).
2. Restrict the comparison to the current viewport or the full overlap range.
3. Normalise fluxes if baseline offsets exist; change the reference trace to explore relative differences.

## 6. Export & Replay

1. From the **Overlay** tab select *Export session*. Choose whether to include CSV dumps, Plotly PNG captures, and manifest metadata.
2. The exported bundle contains `manifest.json`, per-trace data, and a replay helper that rebuilds the overlay layout.
3. Use bundles to share reproducible comparisons or to seed automated regression checks.

## 7. Troubleshooting Tips

- If a file fails to ingest, inspect the ingestion log in the sidebar; malformed headers or unsupported units are called out explicitly.
- Use the trace manager to confirm the detected axis families before running differentials.
- For offline runs, disable live archive previews in Star Hub; cached samples remain available.
- The docs tab (this page) refreshes automatically when Markdown files under `docs/static/` change—use it to surface lab-specific SOPs.

## 8. Getting Help

- Review the citations page for authoritative resources on data provenance and unit conversions.
- Consult `atlas/ui_contract.md` and related atlas docs for deeper architectural notes when extending the application.
