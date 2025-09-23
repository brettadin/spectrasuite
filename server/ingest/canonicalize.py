"""Canonical conversion pipeline for ingested spectra."""

from __future__ import annotations

import numpy as np

from server.ingest.ascii_loader import ASCIIIngestResult
from server.ingest.fits_loader import FITSIngestResult
from server.math import transforms
from server.models import CanonicalSpectrum, ProvenanceEvent, TraceMetadata


def canonicalize_ascii(result: ASCIIIngestResult) -> CanonicalSpectrum:
    """Convert an ASCII ingest result into the canonical spectral representation."""

    metadata = TraceMetadata(
        provider="upload",
        product_id=result.content_hash,
        title=result.label,
        target=result.metadata.target,
        instrument=result.metadata.instrument,
        telescope=result.metadata.telescope,
        wavelength_standard="air" if result.is_air_wavelength else "vacuum",
        flux_units=result.flux_unit or "arbitrary",
        extra=result.metadata.extra,
    )

    provenance = list(result.provenance)

    unit = normalise_wavelength_unit(result.wavelength_unit)
    wavelength_nm = transforms.convert_axis_to_nm(result.wavelength, unit)
    provenance.append(
        ProvenanceEvent(
            step="convert_wavelength_unit",
            parameters={"from": unit, "to": "nm"},
        )
    )

    if result.is_air_wavelength:
        wavelength_nm = transforms.air_to_vacuum(wavelength_nm)
        metadata.wavelength_standard = "vacuum"
        provenance.append(
            ProvenanceEvent(
                step="air_to_vacuum",
                parameters={"method": "edlen1966"},
                note="Converted from stated air wavelengths using Edlén (1966)",
            )
        )

    flux = np.asarray(result.flux, dtype=float)

    canonical = CanonicalSpectrum(
        label=result.label,
        wavelength_vac_nm=np.asarray(wavelength_nm, dtype=float),
        values=flux,
        value_mode="flux_density",
        value_unit=result.flux_unit,
        metadata=metadata,
        provenance=provenance,
        source_hash=result.content_hash,
        uncertainties=result.uncertainties,
    )
    return canonical


def canonicalize_fits(result: FITSIngestResult) -> CanonicalSpectrum:
    """Convert a FITS ingest result into the canonical spectral representation."""

    metadata = TraceMetadata(
        provider=result.metadata.provider or "upload",
        product_id=result.metadata.product_id or result.content_hash,
        title=result.metadata.title or result.label,
        target=result.metadata.target,
        instrument=result.metadata.instrument,
        telescope=result.metadata.telescope,
        ra=result.metadata.ra,
        dec=result.metadata.dec,
        wave_range_nm=None,
        resolving_power=result.metadata.resolving_power,
        wavelength_standard="air" if result.is_air_wavelength else "vacuum",
        flux_units=result.flux_unit or result.metadata.flux_units or "arbitrary",
        pipeline_version=result.metadata.pipeline_version,
        frame=result.metadata.frame,
        radial_velocity_kms=result.metadata.radial_velocity_kms,
        urls=dict(result.metadata.urls),
        citation=result.metadata.citation,
        doi=result.metadata.doi,
        extra=dict(result.metadata.extra),
    )

    provenance = list(result.provenance)

    unit = normalise_wavelength_unit(result.wavelength_unit)
    wavelength_nm = transforms.convert_axis_to_nm(result.wavelength, unit)
    provenance.append(
        ProvenanceEvent(
            step="convert_wavelength_unit",
            parameters={"from": unit, "to": "nm"},
        )
    )

    if result.is_air_wavelength:
        wavelength_nm = transforms.air_to_vacuum(wavelength_nm)
        metadata.wavelength_standard = "vacuum"
        provenance.append(
            ProvenanceEvent(
                step="air_to_vacuum",
                parameters={"method": "edlen1966"},
                note="Converted from stated air wavelengths using Edlén (1966)",
            )
        )

    metadata.wave_range_nm = (
        float(np.nanmin(wavelength_nm)),
        float(np.nanmax(wavelength_nm)),
    )

    canonical = CanonicalSpectrum(
        label=result.label,
        wavelength_vac_nm=np.asarray(wavelength_nm, dtype=float),
        values=np.asarray(result.flux, dtype=float),
        value_mode="flux_density",
        value_unit=result.flux_unit,
        metadata=metadata,
        provenance=provenance,
        source_hash=result.content_hash,
        uncertainties=result.uncertainties,
    )
    return canonical


def normalise_wavelength_unit(unit: str | None) -> transforms.WavelengthUnit:
    if not unit:
        return "nm"
    unit_lc = unit.lower()
    if unit_lc in {"nm", "nanometer", "nanometers"}:
        return "nm"
    if unit_lc in {"angstrom", "angstroms", "a", "aa"}:
        return "angstrom"
    if unit_lc in {"micron", "microns", "um", "µm"}:
        return "micron"
    if unit_lc in {"wavenumber", "cm-1", "cm^-1"}:
        return "wavenumber"
    # default to nm
    return "nm"


__all__ = ["canonicalize_ascii", "canonicalize_fits", "normalise_wavelength_unit"]
