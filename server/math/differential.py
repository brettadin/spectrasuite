"""Differential spectral operations with safeguards."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from server.models import CanonicalSpectrum, ProvenanceEvent, TraceMetadata

EPSILON_DEFAULT = 1e-8


@dataclass(slots=True)
class DifferentialProduct:
    spectrum: CanonicalSpectrum
    operation: str


def _resample(target_wavelengths: np.ndarray, source: CanonicalSpectrum) -> np.ndarray:
    return np.interp(
        target_wavelengths, source.wavelength_vac_nm, source.values, left=np.nan, right=np.nan
    )


def _combine_uncertainties_sum(a: np.ndarray | None, b: np.ndarray | None) -> np.ndarray | None:
    if a is None and b is None:
        return None
    a_arr = np.asarray(a, dtype=float) if a is not None else 0.0
    b_arr = np.asarray(b, dtype=float) if b is not None else 0.0
    return np.sqrt(np.square(a_arr) + np.square(b_arr))


def _combine_uncertainties_ratio(
    result: np.ndarray, a: np.ndarray | None, b: np.ndarray | None
) -> np.ndarray | None:
    if a is None and b is None:
        return None
    result_arr = np.asarray(result, dtype=float)
    a_arr = np.asarray(a, dtype=float) if a is not None else np.zeros_like(result_arr)
    b_arr = np.asarray(b, dtype=float) if b is not None else np.zeros_like(result_arr)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.zeros_like(result_arr)
        mask = result_arr != 0
        rel[mask] = np.sqrt(
            np.square(a_arr[mask] / np.clip(a_arr[mask], EPSILON_DEFAULT, None))
            + np.square(b_arr[mask] / np.clip(b_arr[mask], EPSILON_DEFAULT, None))
        )
    return np.where(mask, rel * np.abs(result_arr), np.nan)


def _create_metadata(base: CanonicalSpectrum, label_suffix: str) -> TraceMetadata:
    metadata = TraceMetadata(
        provider="derived",
        product_id=f"{base.metadata.product_id or base.label}-{label_suffix}",
        title=f"{base.label} {label_suffix}",
        target=base.metadata.target,
        ra=base.metadata.ra,
        dec=base.metadata.dec,
        resolving_power=base.metadata.resolving_power,
        wavelength_standard="vacuum",
        flux_units=base.metadata.flux_units,
        pipeline_version=base.metadata.pipeline_version,
        frame=base.metadata.frame,
        radial_velocity_kms=base.metadata.radial_velocity_kms,
        urls={},
        citation=base.metadata.citation,
        doi=base.metadata.doi,
        extra={"derived_from": base.metadata.to_dict()},
    )
    return metadata


def _identical(a: CanonicalSpectrum, b: CanonicalSpectrum, atol: float = 1e-12) -> bool:
    if a.wavelength_vac_nm.shape != b.wavelength_vac_nm.shape:
        return False
    if not np.allclose(a.wavelength_vac_nm, b.wavelength_vac_nm, atol=atol):
        return False
    if not np.allclose(a.values, b.values, atol=atol):
        return False
    return True


def subtract(
    a: CanonicalSpectrum, b: CanonicalSpectrum, *, epsilon: float = EPSILON_DEFAULT
) -> DifferentialProduct | None:
    if _identical(a, b):
        return None

    target_grid = a.wavelength_vac_nm
    b_resampled = _resample(target_grid, b)
    difference = np.asarray(a.values, dtype=float) - np.asarray(b_resampled, dtype=float)

    uncertainties = _combine_uncertainties_sum(a.uncertainties, b.uncertainties)

    metadata = _create_metadata(a, "minus")
    provenance = a.provenance + [
        ProvenanceEvent(
            step="differential_subtract", parameters={"epsilon": epsilon, "other": b.label}
        )
    ]
    spectrum = CanonicalSpectrum(
        label=f"{a.label}-{b.label}",
        wavelength_vac_nm=target_grid,
        values=difference,
        value_mode=a.value_mode,
        value_unit=a.value_unit,
        metadata=metadata,
        provenance=provenance,
        source_hash=None,
        uncertainties=uncertainties,
    )
    return DifferentialProduct(spectrum=spectrum, operation="subtract")


def divide(
    a: CanonicalSpectrum, b: CanonicalSpectrum, *, epsilon: float = EPSILON_DEFAULT
) -> DifferentialProduct | None:
    if _identical(a, b):
        return None

    target_grid = a.wavelength_vac_nm
    b_resampled = _resample(target_grid, b)
    denominator = np.asarray(b_resampled, dtype=float)
    result = np.asarray(a.values, dtype=float) / np.clip(denominator, epsilon, None)
    uncertainties = _combine_uncertainties_ratio(result, a.uncertainties, b.uncertainties)

    metadata = _create_metadata(a, "divided")
    provenance = a.provenance + [
        ProvenanceEvent(
            step="differential_divide", parameters={"epsilon": epsilon, "other": b.label}
        )
    ]
    spectrum = CanonicalSpectrum(
        label=f"{a.label}/{b.label}",
        wavelength_vac_nm=target_grid,
        values=result,
        value_mode="relative_intensity",
        value_unit=None,
        metadata=metadata,
        provenance=provenance,
        source_hash=None,
        uncertainties=uncertainties,
    )
    return DifferentialProduct(spectrum=spectrum, operation="divide")


__all__ = ["DifferentialProduct", "divide", "subtract"]
