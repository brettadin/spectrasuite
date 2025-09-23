"""Shared data models for spectra and provenance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

import numpy as np

ValueMode = Literal[
    "flux_density",
    "relative_intensity",
    "transmission",
    "absorbance",
    "optical_depth",
]


@dataclass(slots=True)
class ProvenanceEvent:
    """Record a deterministic transform applied to a spectrum."""

    step: str
    parameters: dict[str, Any] = field(default_factory=dict)
    note: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "parameters": self.parameters,
            "note": self.note,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ProvenanceEvent:
        timestamp_raw = payload.get("timestamp")
        timestamp = (
            datetime.fromisoformat(timestamp_raw)
            if isinstance(timestamp_raw, str)
            else datetime.now(UTC)
        )
        return cls(
            step=payload["step"],
            parameters=dict(payload.get("parameters", {})),
            note=payload.get("note"),
            timestamp=timestamp,
        )


@dataclass(slots=True)
class TraceMetadata:
    """Metadata associated with a spectrum trace."""

    provider: str | None = None
    product_id: str | None = None
    title: str | None = None
    target: str | None = None
    instrument: str | None = None
    telescope: str | None = None
    ra: float | None = None
    dec: float | None = None
    wave_range_nm: tuple[float, float] | None = None
    resolving_power: float | None = None
    wavelength_standard: Literal["air", "vacuum", "unknown"] | None = None
    flux_units: str | None = None
    pipeline_version: str | None = None
    frame: Literal["topocentric", "heliocentric", "barycentric", "unknown", "none"] | None = None
    radial_velocity_kms: float | None = None
    urls: dict[str, str] = field(default_factory=dict)
    citation: str | None = None
    doi: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "product_id": self.product_id,
            "title": self.title,
            "target": self.target,
            "instrument": self.instrument,
            "telescope": self.telescope,
            "ra": self.ra,
            "dec": self.dec,
            "wave_range_nm": list(self.wave_range_nm) if self.wave_range_nm else None,
            "resolving_power": self.resolving_power,
            "wavelength_standard": self.wavelength_standard,
            "flux_units": self.flux_units,
            "pipeline_version": self.pipeline_version,
            "frame": self.frame,
            "radial_velocity_kms": self.radial_velocity_kms,
            "urls": self.urls,
            "citation": self.citation,
            "doi": self.doi,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TraceMetadata:
        wave_range = payload.get("wave_range_nm")
        wave_range_tuple = None
        if isinstance(wave_range, list | tuple) and len(wave_range) == 2:
            wave_range_tuple = (float(wave_range[0]), float(wave_range[1]))
        return cls(
            provider=payload.get("provider"),
            product_id=payload.get("product_id"),
            title=payload.get("title"),
            target=payload.get("target"),
            instrument=payload.get("instrument"),
            telescope=payload.get("telescope"),
            ra=payload.get("ra"),
            dec=payload.get("dec"),
            wave_range_nm=wave_range_tuple,
            resolving_power=payload.get("resolving_power"),
            wavelength_standard=payload.get("wavelength_standard"),
            flux_units=payload.get("flux_units"),
            pipeline_version=payload.get("pipeline_version"),
            frame=payload.get("frame"),
            radial_velocity_kms=payload.get("radial_velocity_kms"),
            urls=dict(payload.get("urls", {})),
            citation=payload.get("citation"),
            doi=payload.get("doi"),
            extra=dict(payload.get("extra", {})),
        )


@dataclass(slots=True)
class CanonicalSpectrum:
    """Spectrum data normalized to the canonical wavelength baseline."""

    label: str
    wavelength_vac_nm: np.ndarray
    values: np.ndarray
    value_mode: ValueMode
    value_unit: str | None
    metadata: TraceMetadata
    provenance: list[ProvenanceEvent] = field(default_factory=list)
    source_hash: str | None = None
    uncertainties: np.ndarray | None = None

    def to_manifest_entry(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "wavelength_vac_nm": self.wavelength_vac_nm.tolist(),
            "values": self.values.tolist(),
            "value_mode": self.value_mode,
            "value_unit": self.value_unit,
            "metadata": self.metadata.to_dict(),
            "provenance": [event.to_dict() for event in self.provenance],
            "source_hash": self.source_hash,
            "uncertainties": (
                self.uncertainties.tolist() if self.uncertainties is not None else None
            ),
        }

    @classmethod
    def from_manifest_entry(cls, payload: dict[str, Any]) -> CanonicalSpectrum:
        provenance_payload = payload.get("provenance", [])
        provenance = [ProvenanceEvent.from_dict(item) for item in provenance_payload]
        uncertainties_raw = payload.get("uncertainties")
        uncertainties = None
        if uncertainties_raw is not None:
            uncertainties = np.asarray(uncertainties_raw, dtype=float)
        return cls(
            label=payload["label"],
            wavelength_vac_nm=np.asarray(payload["wavelength_vac_nm"], dtype=float),
            values=np.asarray(payload["values"], dtype=float),
            value_mode=payload.get("value_mode", "flux_density"),
            value_unit=payload.get("value_unit"),
            metadata=TraceMetadata.from_dict(payload.get("metadata", {})),
            provenance=provenance,
            source_hash=payload.get("source_hash"),
            uncertainties=uncertainties,
        )


__all__ = [
    "CanonicalSpectrum",
    "ProvenanceEvent",
    "TraceMetadata",
    "ValueMode",
]
