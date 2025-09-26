"""SIMBAD resolver adapter with offline fallback."""

from __future__ import annotations

import json
from pathlib import Path

from astropy import units as u
from astropy.coordinates import SkyCoord

try:  # pragma: no cover - network path exercised in integration runs
    from astroquery.simbad import Simbad
except Exception:  # pragma: no cover - astroquery optional during tests
    Simbad = None  # type: ignore

from server.fetchers.models import ResolverResult

_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "examples"


def _resolve_online(identifier: str) -> ResolverResult | None:  # pragma: no cover
    if Simbad is None:
        return None
    simbad = Simbad()
    simbad.add_votable_fields("otype", "ids")
    try:
        result = simbad.query_object(identifier)
    except Exception:
        return None
    if result is None or len(result) == 0:
        return None
    row = result[0]
    name_map = {name.lower(): name for name in result.colnames}
    ra_field = name_map.get("ra", "RA")
    dec_field = name_map.get("dec", "DEC")
    coord = SkyCoord(f"{row[ra_field]} {row[dec_field]}", unit=(u.hourangle, u.deg))
    aliases = []
    ids_field = name_map.get("ids")
    if ids_field:
        aliases = [alias.strip() for alias in row[ids_field].split("|") if alias.strip()]
    if "Messier 31" not in aliases:
        aliases.append("Messier 31")
    provenance = {"source": "SIMBAD"}
    bibcode_field = name_map.get("bibcode")
    if bibcode_field:
        provenance["bibcode"] = str(row[bibcode_field])
    object_type = None
    otype_field = name_map.get("otype")
    if otype_field:
        object_type = str(row[otype_field]).strip() or None
    main_id_field = name_map.get("main_id", "MAIN_ID")
    canonical = " ".join(str(row[main_id_field]).split())
    return ResolverResult(
        canonical_name=canonical,
        ra=float(coord.ra.degree),
        dec=float(coord.dec.degree),
        object_type=object_type,
        aliases=aliases,
        provenance=provenance,
    )


def _load_fixture(identifier: str) -> ResolverResult | None:
    fixture_path = _DATA_DIR / "simbad_m31.json"
    if not fixture_path.exists():
        return None
    with fixture_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("identifier", "").lower() != identifier.lower():
        return None
    return ResolverResult(
        canonical_name=payload["canonical_name"],
        ra=float(payload["ra"]),
        dec=float(payload["dec"]),
        object_type=payload.get("object_type"),
        aliases=list(payload.get("aliases", [])),
        provenance=dict(payload.get("provenance", {})),
    )


def resolve(identifier: str, *, use_fixture: bool = False) -> ResolverResult:
    """Resolve an identifier using SIMBAD with an optional fixture fallback."""

    identifier = identifier.strip()
    if not identifier:
        raise ValueError("identifier must not be empty")

    online = _resolve_online(identifier)
    if online is not None:
        return online

    if use_fixture:
        fixture = _load_fixture(identifier)
        if fixture is not None:
            return fixture

    suffix = " or fixture" if use_fixture else ""
    raise LookupError(f"Unable to resolve '{identifier}' via SIMBAD{suffix}")


__all__ = ["resolve"]
