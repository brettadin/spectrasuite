from __future__ import annotations

from server.fetchers import resolver_simbad


def test_resolver_fixture_m31() -> None:
    result = resolver_simbad.resolve("M 31")
    assert result.canonical_name == "M 31"
    assert result.ra is not None and result.dec is not None
    assert "Messier 31" in result.aliases
