"""Atomic and molecular line overlay utilities."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from server.math.transforms import doppler_shift_wavelength

_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "examples"


@dataclass(slots=True)
class LineEntry:
    species: str
    wavelength_nm: float
    relative_intensity: float
    log_gf: float | None = None
    Aki: float | None = None


@dataclass(slots=True)
class ScaledLine:
    species: str
    wavelength_nm: float
    display_height: float
    relative_intensity: float
    metadata: dict


class LineCatalog:
    """Load static line data from local fixtures."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (_DATA_DIR / "nist_fe_lines.csv")
        if not self._path.exists():
            raise FileNotFoundError(f"Line catalog not found: {self._path}")
        self._frame = pd.read_csv(self._path)

    def species(self) -> list[str]:
        return sorted({str(value).strip() for value in self._frame["species"].unique()})

    def lines_for_species(self, species: str) -> list[LineEntry]:
        subset = self._frame[self._frame["species"].str.lower() == species.lower()]
        entries = []
        for _, row in subset.iterrows():
            entries.append(
                LineEntry(
                    species=row["species"],
                    wavelength_nm=float(row["wavelength_nm"]),
                    relative_intensity=float(row["relative_intensity"]),
                    log_gf=float(row["log_gf"]) if not pd.isna(row["log_gf"]) else None,
                    Aki=float(row["Aki"]) if not pd.isna(row["Aki"]) else None,
                )
            )
        return entries


def scale_lines(
    entries: Iterable[LineEntry],
    *,
    mode: str = "relative",
    gamma: float = 1.0,
    min_relative_intensity: float = 0.0,
) -> list[ScaledLine]:
    entries_list = list(entries)
    if not entries_list:
        return []

    intensities = np.array([entry.relative_intensity for entry in entries_list], dtype=float)
    if np.all(intensities <= 0):
        intensities = np.ones_like(intensities)

    if mode == "relative":
        normaliser = np.max(intensities)
    elif mode == "quantile":
        normaliser = np.quantile(intensities, 0.99)
    else:
        raise ValueError(f"Unsupported scaling mode: {mode}")

    if normaliser <= 0:
        normaliser = np.max(intensities)
    scaled = np.clip(intensities / normaliser, 0.0, 1.0)
    scaled = np.power(scaled, gamma)

    result: list[ScaledLine] = []
    for entry, relative_height, scale in zip(entries_list, intensities, scaled, strict=False):
        if normaliser > 0 and (relative_height / normaliser) < min_relative_intensity:
            continue
        result.append(
            ScaledLine(
                species=entry.species,
                wavelength_nm=entry.wavelength_nm,
                display_height=float(scale),
                relative_intensity=float(relative_height),
                metadata={"log_gf": entry.log_gf, "Aki": entry.Aki},
            )
        )
    return result


def apply_velocity_shift(lines: Iterable[ScaledLine], velocity_kms: float) -> list[ScaledLine]:
    shifted: list[ScaledLine] = []
    for line in lines:
        shifted.append(
            ScaledLine(
                species=line.species,
                wavelength_nm=float(
                    doppler_shift_wavelength(np.array([line.wavelength_nm]), velocity_kms)[0]
                ),
                display_height=line.display_height,
                relative_intensity=line.relative_intensity,
                metadata=line.metadata,
            )
        )
    return shifted


__all__ = ["LineCatalog", "LineEntry", "ScaledLine", "apply_velocity_shift", "scale_lines"]
