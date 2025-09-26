"""Tests for similarity analysis helpers."""

from __future__ import annotations

import numpy as np
import pytest

from server.analysis.similarity import (
    SimilarityCache,
    SimilarityOptions,
    TraceVectors,
    apply_normalization,
    build_metric_frames,
    viewport_alignment,
)


def _make_trace(
    trace_id: str,
    wavelengths: list[float],
    values: list[float],
    *,
    fingerprint: str | None = None,
) -> TraceVectors:
    return TraceVectors(
        trace_id=trace_id,
        label=trace_id,
        wavelengths_nm=np.array(wavelengths, dtype=float),
        flux=np.array(values, dtype=float),
        fingerprint=fingerprint,
    )


def test_similarity_cosine_and_rmse() -> None:
    trace_a = _make_trace("a", [500.0, 501.0, 502.0], [1.0, 2.0, 3.0])
    trace_b = _make_trace("b", [500.0, 501.0, 502.0], [1.0, 2.0, 3.0])
    cache = SimilarityCache()
    options = SimilarityOptions(metrics=("cosine", "rmse"))

    metrics = cache.compute(trace_a, trace_b, (None, None), options)

    assert pytest.approx(metrics["cosine"], rel=1e-6) == 1.0
    assert pytest.approx(metrics["rmse"], rel=1e-6) == 0.0
    assert metrics["points"] == 3.0


def test_similarity_cache_symmetric_results() -> None:
    trace_a = _make_trace("a", [500.0, 501.0], [1.0, 0.0], fingerprint="hash-a")
    trace_b = _make_trace("b", [500.0, 501.0], [0.5, 0.5], fingerprint="hash-b")
    cache = SimilarityCache()
    options = SimilarityOptions(metrics=("cosine",))

    forward = cache.compute(trace_a, trace_b, (None, None), options)
    reverse = cache.compute(trace_b, trace_a, (None, None), options)

    assert forward == reverse
    assert "cosine" in forward


def test_apply_normalization_modes() -> None:
    values = np.array([1.0, 2.0, 3.0], dtype=float)
    unit = apply_normalization(values, "unit")
    assert pytest.approx(np.linalg.norm(unit), rel=1e-6) == 1.0

    peak = apply_normalization(values, "max")
    assert pytest.approx(peak.max(), rel=1e-6) == 1.0

    zscore = apply_normalization(values, "zscore")
    assert pytest.approx(np.mean(zscore), abs=1e-6) == 0.0


def test_build_metric_frames_produces_symmetry() -> None:
    trace_a = _make_trace("a", [500.0, 501.0], [1.0, 0.0])
    trace_b = _make_trace("b", [500.0, 501.0], [0.5, 0.5])
    cache = SimilarityCache()
    options = SimilarityOptions(metrics=("cosine", "rmse"))

    frames, labels = build_metric_frames([trace_a, trace_b], (None, None), options, cache)

    assert set(frames.keys()) == {"cosine", "rmse"}
    cosine = frames["cosine"]
    rmse = frames["rmse"]
    assert cosine.loc["a", "a"] == 1.0
    assert rmse.loc["a", "a"] == 0.0
    assert cosine.loc["a", "b"] == cosine.loc["b", "a"]
    assert labels["a"] == "a"


def test_viewport_alignment_filters_wavelength_range() -> None:
    trace_a = _make_trace("a", [500.0, 501.0, 502.0], [1.0, 2.0, 3.0])
    trace_b = _make_trace("b", [501.0, 502.0, 503.0], [0.0, 1.0, 2.0])

    axis, values_a, values_b = viewport_alignment(trace_a, trace_b, (501.0, 502.0))

    assert axis is not None and values_a is not None and values_b is not None
    assert axis[0] >= 501.0
    assert axis[-1] <= 502.0
    assert len(axis) == len(values_a) == len(values_b)
