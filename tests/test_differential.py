from __future__ import annotations

import numpy as np

from server.math.differential import divide, subtract
from server.models import CanonicalSpectrum, TraceMetadata


def _make_trace(label: str, values: np.ndarray) -> CanonicalSpectrum:
    return CanonicalSpectrum(
        label=label,
        wavelength_vac_nm=np.linspace(500.0, 501.0, len(values)),
        values=values,
        value_mode="flux_density",
        value_unit="arb",
        metadata=TraceMetadata(provider="test"),
        provenance=[],
        source_hash=label,
    )


def test_identical_traces_suppressed() -> None:
    values = np.array([1.0, 2.0, 3.0])
    trace_a = _make_trace("A", values)
    trace_b = _make_trace("B", values)
    assert subtract(trace_a, trace_b) is None
    assert divide(trace_a, trace_b) is None


def test_subtract_and_divide() -> None:
    trace_a = _make_trace("A", np.array([2.0, 4.0, 6.0]))
    trace_b = _make_trace("B", np.array([1.0, 2.0, 3.0]))
    subtraction = subtract(trace_a, trace_b)
    assert subtraction is not None
    np.testing.assert_allclose(subtraction.spectrum.values, [1.0, 2.0, 3.0])
    ratio = divide(trace_a, trace_b)
    assert ratio is not None
    np.testing.assert_allclose(ratio.spectrum.values, [2.0, 2.0, 2.0])
