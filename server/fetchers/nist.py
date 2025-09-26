"""NIST Atomic Spectra Database integration utilities."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np

try:  # pragma: no cover - optional dependency in CI
    from astroquery.nist import Nist as _AstroqueryNist
except Exception:  # pragma: no cover - astroquery is optional for tests
    _AstroqueryNist = None  # type: ignore[assignment]

_CACHE_VERSION = 1
_DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache" / "nist"
_DEFAULT_OFFLINE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "examples" / "nist_offline.json"
)


class NistUnavailableError(RuntimeError):
    """Raised when the NIST service cannot be reached and no cache is available."""


@dataclass(slots=True)
class _NormalisedRow:
    wavelength_nm: float
    relative_intensity: float
    ritz_wavelength_nm: float | None = None
    observed_wavelength_nm: float | None = None
    transition: str | None = None
    lower_level: str | None = None
    upper_level: str | None = None
    configuration: str | None = None
    Aki: float | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "wavelength_nm": self.wavelength_nm,
            "relative_intensity": self.relative_intensity,
            "ritz_wavelength_nm": self.ritz_wavelength_nm,
            "observed_wavelength_nm": self.observed_wavelength_nm,
            "transition": self.transition,
            "lower_level": self.lower_level,
            "upper_level": self.upper_level,
            "configuration": self.configuration,
            "Aki": self.Aki,
            "notes": self.notes,
        }


def _slugify(value: str) -> str:
    cleaned = "".join(char if char.isalnum() else "-" for char in value.lower())
    return "-".join(part for part in cleaned.split("-") if part) or "species"


def _angstrom_to_nm(value: float | None) -> float | None:
    if value is None:
        return None
    return float(value) / 10.0


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if math.isnan(float(value)):
            return None
        return float(value)
    if isinstance(value, np.ndarray):  # pragma: no cover - defensive
        if value.size == 0:
            return None
        return _coerce_float(value.item())
    try:
        text = str(value).strip()
    except Exception:  # pragma: no cover - defensive
        return None
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if math.isnan(number):
        return None
    return number


def _coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    text = str(value).strip()
    return text or None


def _table_value(table: Any, row: Any, candidates: Iterable[str]) -> Any:
    colnames = getattr(table, "colnames", [])
    for candidate in candidates:
        if candidate in colnames:
            try:
                value = row[candidate]
            except Exception:  # pragma: no cover - defensive access
                continue
            if getattr(value, "mask", False) is True:
                continue
            coerced = getattr(value, "filled", lambda: value)()
            if coerced is np.ma.masked:  # type: ignore[attr-defined]
                continue
            return coerced
    return None


def _normalise_row(table: Any, row: Any) -> _NormalisedRow | None:
    observed_angstrom = _coerce_float(
        _table_value(
            table,
            row,
            (
                "Observed Wavelength",
                "obs_wl_vac_(A)",
                "obs_wl_air_(A)",
                "Observed",
            ),
        )
    )
    ritz_angstrom = _coerce_float(
        _table_value(
            table,
            row,
            (
                "Ritz",
                "Ritz Wavelength",
                "ritz_wl_vac_(A)",
                "ritz_wl_air_(A)",
            ),
        )
    )
    rel_intensity = _coerce_float(
        _table_value(
            table,
            row,
            (
                "Rel. Int.",
                "RI",
                "Intensity",
                "Rel_Intensity",
            ),
        )
    )
    wavelength_angstrom = ritz_angstrom or observed_angstrom
    if wavelength_angstrom is None:
        return None
    if rel_intensity is None:
        rel_intensity = 0.0

    transition = _coerce_str(
        _table_value(
            table,
            row,
            (
                "Transition",
                "Transition Ref.",
                "Transition Reference",
                "TransitionRef",
            ),
        )
    )
    lower = _coerce_str(
        _table_value(
            table,
            row,
            (
                "Lower level",
                "Lower Level",
                "Lower Level (J)",
                "Lower level (cm-1)",
                "Lower",
            ),
        )
    )
    upper = _coerce_str(
        _table_value(
            table,
            row,
            (
                "Upper level",
                "Upper Level",
                "Upper Level (J)",
                "Upper",
            ),
        )
    )
    configuration = _coerce_str(
        _table_value(
            table,
            row,
            (
                "Configuration",
                "Electron Configuration",
                "Config.",
            ),
        )
    )
    Aki = _coerce_float(
        _table_value(
            table,
            row,
            (
                "Aki",
                "Aki (s-1)",
                "Aki (s^-1)",
                "A_{ki}",
            ),
        )
    )
    notes = _coerce_str(
        _table_value(
            table,
            row,
            (
                "Notes",
                "Line Ref.",
                "Comment",
            ),
        )
    )

    return _NormalisedRow(
        wavelength_nm=float(_angstrom_to_nm(wavelength_angstrom)),
        relative_intensity=float(rel_intensity),
        ritz_wavelength_nm=_angstrom_to_nm(ritz_angstrom),
        observed_wavelength_nm=_angstrom_to_nm(observed_angstrom),
        transition=transition,
        lower_level=lower,
        upper_level=upper,
        configuration=configuration,
        Aki=Aki,
        notes=notes,
    )


def _table_to_rows(table: Any) -> list[dict[str, Any]]:
    rows: list[_NormalisedRow] = []
    for entry in table:
        normalised = _normalise_row(table, entry)
        if normalised is None:
            continue
        rows.append(normalised)
    rows.sort(key=lambda item: item.wavelength_nm)
    return [row.to_dict() for row in rows]


def _remote_fetch(
    species: str,
    wavelength_min_nm: float,
    wavelength_max_nm: float,
    *,
    use_ritz_wavelength: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if _AstroqueryNist is None:
        raise RuntimeError("astroquery.nist is not available")
    range_angstrom = f"{wavelength_min_nm * 10:.3f}-{wavelength_max_nm * 10:.3f}"
    try:
        table = _AstroqueryNist.query(
            wavelength_range=range_angstrom,
            spectrum=species,
            wavelength_type="vacuum" if use_ritz_wavelength else "air",
            linelist="Atomic",
        )
    except Exception as exc:  # pragma: no cover - network failure path
        raise RuntimeError("NIST query failed") from exc
    if table is None:
        return [], {"source": "nist_api", "query": range_angstrom}
    rows = _table_to_rows(table)
    return rows, {"source": "nist_api", "query": range_angstrom}


def _load_offline_catalog(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text())
    except Exception:  # pragma: no cover - malformed fixture
        return []
    entries = payload.get("entries")
    if not isinstance(entries, list):
        return []
    result: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        try:
            wavelength = float(entry["wavelength_nm"])
            intensity = float(entry.get("relative_intensity", 0.0))
        except Exception:
            continue
        record = dict(entry)
        record["wavelength_nm"] = wavelength
        record["relative_intensity"] = intensity
        result.append(record)
    result.sort(key=lambda item: item["wavelength_nm"])
    return result


def _offline_fallback(
    species: str,
    wavelength_min_nm: float,
    wavelength_max_nm: float,
    *,
    offline_catalog: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    rows = _load_offline_catalog(offline_catalog)
    if not rows:
        return None
    filtered = [
        row
        for row in rows
        if row.get("species", "").lower() == species.lower()
        and wavelength_min_nm <= float(row.get("wavelength_nm", 0.0)) <= wavelength_max_nm
    ]
    if not filtered:
        return None
    return filtered, {"source": "offline", "catalog": str(offline_catalog)}


def _cache_filename(
    species: str,
    wavelength_min_nm: float,
    wavelength_max_nm: float,
    *,
    use_ritz_wavelength: bool,
) -> str:
    slug = _slugify(species)
    window = f"{wavelength_min_nm:.3f}-{wavelength_max_nm:.3f}"
    mode = "ritz" if use_ritz_wavelength else "observed"
    return f"{slug}_{window}_{mode}.json"


def _read_cache(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except Exception:
        return None
    if payload.get("version") != _CACHE_VERSION:
        return None
    rows = payload.get("rows")
    metadata = payload.get("metadata", {})
    if not isinstance(rows, list):
        return None
    return rows, metadata


def _write_cache(path: Path, rows: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
    payload = {
        "version": _CACHE_VERSION,
        "rows": rows,
        "metadata": metadata,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def fetch_lines(
    species: str,
    wavelength_min_nm: float,
    wavelength_max_nm: float,
    *,
    use_ritz_wavelength: bool = True,
    cache_dir: Path | None = None,
    offline_catalog: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch spectral line data from the NIST ASD, with caching and fallback."""

    if wavelength_min_nm >= wavelength_max_nm:
        raise ValueError("Minimum wavelength must be less than maximum wavelength")

    cache_root = cache_dir or _DEFAULT_CACHE_DIR
    offline_path = offline_catalog or _DEFAULT_OFFLINE_PATH
    cache_file = cache_root / _cache_filename(
        species,
        wavelength_min_nm,
        wavelength_max_nm,
        use_ritz_wavelength=use_ritz_wavelength,
    )

    cached_rows: list[dict[str, Any]] | None = None
    cached_metadata: dict[str, Any] | None = None
    cached = _read_cache(cache_file)
    if cached is not None:
        cached_rows, cached_metadata = cached

    try:
        rows, remote_meta = _remote_fetch(
            species,
            wavelength_min_nm,
            wavelength_max_nm,
            use_ritz_wavelength=use_ritz_wavelength,
        )
        fetched_at = datetime.now(UTC).isoformat()
        cache_metadata = {
            "fetched_at": fetched_at,
            "source": remote_meta.get("source", "nist_api"),
            "offline_fallback": False,
        }
        _write_cache(cache_file, rows, cache_metadata)
        metadata = {
            "species": species,
            "wavelength_window_nm": (wavelength_min_nm, wavelength_max_nm),
            "use_ritz_wavelength": use_ritz_wavelength,
            "cache_hit": False,
            "fetched_at": fetched_at,
            "row_count": len(rows),
            "cache_path": str(cache_file),
            "source": remote_meta.get("source", "nist_api"),
            "query": remote_meta.get("query"),
        }
        return rows, metadata
    except Exception as exc:
        if cached_rows is not None and cached_metadata is not None:
            metadata = {
                "species": species,
                "wavelength_window_nm": (wavelength_min_nm, wavelength_max_nm),
                "use_ritz_wavelength": use_ritz_wavelength,
                "cache_hit": True,
                "fetched_at": cached_metadata.get("fetched_at"),
                "cached_at": cached_metadata.get("fetched_at"),
                "row_count": len(cached_rows),
                "cache_path": str(cache_file),
                "source": cached_metadata.get("source", "cache"),
                "error": str(exc),
            }
            if cached_metadata.get("offline_fallback"):
                metadata["offline_fallback"] = True
            return cached_rows, metadata

        offline = _offline_fallback(
            species,
            wavelength_min_nm,
            wavelength_max_nm,
            offline_catalog=offline_path,
        )
        if offline is not None:
            rows, offline_meta = offline
            fetched_at = datetime.now(UTC).isoformat()
            metadata = {
                "species": species,
                "wavelength_window_nm": (wavelength_min_nm, wavelength_max_nm),
                "use_ritz_wavelength": use_ritz_wavelength,
                "cache_hit": False,
                "offline_fallback": True,
                "fetched_at": fetched_at,
                "row_count": len(rows),
                "source": offline_meta.get("source", "offline"),
                "catalog": offline_meta.get("catalog"),
                "error": str(exc),
            }
            try:
                cache_metadata = {
                    "fetched_at": fetched_at,
                    "source": metadata["source"],
                    "offline_fallback": True,
                    "error": str(exc),
                }
                _write_cache(cache_file, rows, cache_metadata)
                metadata["cache_path"] = str(cache_file)
            except Exception:  # pragma: no cover - cache write best effort
                pass
            return rows, metadata
        raise NistUnavailableError(
            "NIST ASD service unavailable and no cached/offline data present"
        ) from exc


__all__ = ["NistUnavailableError", "fetch_lines"]
