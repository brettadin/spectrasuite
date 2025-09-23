from __future__ import annotations

import numpy as np

from server.overlays.lines import LineCatalog, scale_lines


def test_scale_lines_relative_and_quantile() -> None:
    catalog = LineCatalog()
    entries = catalog.lines_for_species("Fe I")
    relative = scale_lines(entries, mode="relative", gamma=1.0)
    assert relative
    heights = np.array([line.display_height for line in relative])
    assert np.isclose(np.max(heights), 1.0)

    quantile = scale_lines(entries, mode="quantile", gamma=1.0)
    heights_quantile = np.array([line.display_height for line in quantile])
    assert np.max(heights_quantile) <= 1.0
    assert np.median(heights_quantile) > 0
