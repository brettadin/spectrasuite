from __future__ import annotations

import json
import pytest

from server.fetchers import nist


_SAMPLE_ROWS = [
    {
        "wavelength_nm": 500.0,
        "relative_intensity": 120.0,
        "ritz_wavelength_nm": 500.0,
        "observed_wavelength_nm": 500.0,
        "transition": "a - b",
    }
]


def test_fetch_lines_writes_and_reads_cache(tmp_path, monkeypatch) -> None:
    cache_dir = tmp_path / "cache"

    def fake_remote(species, wmin, wmax, *, use_ritz_wavelength):
        assert species == "Fe I"
        assert wmin == pytest.approx(500.0)
        assert wmax == pytest.approx(501.0)
        assert use_ritz_wavelength is True
        return list(_SAMPLE_ROWS), {"source": "test", "query": "5000-5010"}

    monkeypatch.setattr(nist, "_remote_fetch", fake_remote)

    rows, metadata = nist.fetch_lines(
        "Fe I", 500.0, 501.0, cache_dir=cache_dir, use_ritz_wavelength=True
    )
    assert rows == _SAMPLE_ROWS
    assert metadata["cache_hit"] is False
    cache_files = list(cache_dir.rglob("*.json"))
    assert len(cache_files) == 1

    def failing_remote(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(nist, "_remote_fetch", failing_remote)

    rows_cached, metadata_cached = nist.fetch_lines(
        "Fe I", 500.0, 501.0, cache_dir=cache_dir, use_ritz_wavelength=True
    )
    assert rows_cached == _SAMPLE_ROWS
    assert metadata_cached["cache_hit"] is True
    assert "boom" in metadata_cached["error"]


def test_fetch_lines_offline_fallback(tmp_path, monkeypatch) -> None:
    offline_catalog = tmp_path / "offline.json"
    offline_payload = {
        "entries": [
            {
                "species": "Fe I",
                "wavelength_nm": 500.5,
                "relative_intensity": 80.0,
            }
        ]
    }
    offline_catalog.write_text(json.dumps(offline_payload))

    def failing_remote(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(nist, "_remote_fetch", failing_remote)

    rows, metadata = nist.fetch_lines(
        "Fe I",
        500.0,
        501.0,
        cache_dir=tmp_path / "cache",
        offline_catalog=offline_catalog,
    )
    assert rows[0]["wavelength_nm"] == pytest.approx(500.5)
    assert metadata["offline_fallback"] is True
    assert metadata["cache_hit"] is False
    assert "network down" in metadata["error"]


def test_fetch_lines_raises_without_fallback(tmp_path, monkeypatch) -> None:
    def failing_remote(*args, **kwargs):
        raise RuntimeError("no service")

    monkeypatch.setattr(nist, "_remote_fetch", failing_remote)

    cache_dir = tmp_path / "cache"
    with pytest.raises(nist.NistUnavailableError):
        nist.fetch_lines(
            "Fe I",
            500.0,
            501.0,
            cache_dir=cache_dir,
            offline_catalog=tmp_path / "missing.json",
        )
