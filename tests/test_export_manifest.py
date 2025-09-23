from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from app.state.session import AppSessionState, XAxisUnit
from server.export.manifest import export_session, replay_manifest
from server.ingest.ascii_loader import load_ascii_spectrum
from server.ingest.canonicalize import canonicalize_ascii


def _session_with_example() -> AppSessionState:
    fixture = Path("data/examples/example_spectrum.csv")
    result = load_ascii_spectrum(fixture.read_bytes(), fixture.name)
    canonical = canonicalize_ascii(result)
    session = AppSessionState()
    session.register_trace(canonical)
    return session


def test_export_manifest_and_replay() -> None:
    session = _session_with_example()
    bundle = export_session(
        session,
        figure=None,
        app_version="0.1.0b",
        schema_version=2,
        axis_unit=XAxisUnit.NM,
        display_mode=session.display_mode.value,
        overlay_settings={"line_overlay": {"species": "Fe I"}},
        include_png=False,
    )
    with ZipFile(BytesIO(bundle.zip_bytes)) as archive:
        assert "manifest.json" in archive.namelist()
        manifest_payload = json.loads(archive.read("manifest.json"))
    spectra = replay_manifest(manifest_payload)
    assert len(spectra) == 1
    assert spectra[0].label == session.traces[session.trace_order[0]].label
