"""Analytical helpers for spectral comparison."""

from .similarity import (
    SimilarityCache,
    SimilarityOptions,
    TraceVectors,
    apply_normalization,
    build_metric_frames,
    viewport_alignment,
)

__all__ = [
    "SimilarityCache",
    "SimilarityOptions",
    "TraceVectors",
    "apply_normalization",
    "build_metric_frames",
    "viewport_alignment",
]
