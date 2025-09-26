from __future__ import annotations

import numpy as np

from server.ingest.nist_lines import to_canonical


def test_to_canonical_metadata_and_provenance() -> None:
    rows = [
        {
            "wavelength_nm": 500.0,
            "relative_intensity": 120.0,
            "ritz_wavelength_nm": 500.0,
            "transition": "a - b",
        },
        {
            "wavelength_nm": 501.0,
            "relative_intensity": 80.0,
            "ritz_wavelength_nm": 501.0,
            "transition": "b - c",
        },
    ]
    metadata = {
        "species": "Fe I",
        "wavelength_window_nm": (499.5, 501.5),
        "use_ritz_wavelength": True,
        "cache_hit": True,
        "offline_fallback": False,
        "fetched_at": "2024-01-01T00:00:00+00:00",
        "source": "cache",
    }

    canonical = to_canonical(rows, metadata, app_version="1.2.3")

    assert canonical.label.startswith("NIST lines: Fe I")
    assert canonical.value_mode == "relative_intensity"
    assert canonical.metadata.provider == "NIST ASD"
    extra = canonical.metadata.extra["nist"]
    assert extra["cache_hit"] is True
    assert extra["row_count"] == 2
    assert extra["rows"][0]["transition"] == "a - b"
    event = canonical.provenance[0]
    assert event.step == "fetch_nist_lines"
    assert event.parameters["species"] == "Fe I"
    assert event.parameters["app_version"] == "1.2.3"
    assert event.parameters["cache_hit"] is True
    assert np.allclose(canonical.wavelength_vac_nm, np.array([500.0, 501.0]))
    assert np.allclose(canonical.values, np.array([120.0, 80.0]))


def test_to_canonical_rejects_empty_rows() -> None:
    try:
        to_canonical([], {"species": "Fe I"}, app_version="1.0.0")
    except ValueError as exc:
        assert "No valid NIST lines" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected ValueError for empty rows")
