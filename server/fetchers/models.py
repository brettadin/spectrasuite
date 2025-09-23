"""Data models for archive fetchers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(slots=True)
class Product:
    provider: str
    product_id: str
    title: str
    target: str | None
    ra: float | None
    dec: float | None
    wave_range_nm: tuple[float, float] | None
    resolution_R: float | None
    wavelength_standard: Literal["air", "vacuum", "unknown", "mixed", "none"] | None
    flux_units: str | None
    pipeline_version: str | None
    urls: dict[str, str] = field(default_factory=dict)
    citation: str | None = None
    doi: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ResolverResult:
    canonical_name: str
    ra: float | None
    dec: float | None
    object_type: str | None
    aliases: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)


__all__ = ["Product", "ResolverResult"]
