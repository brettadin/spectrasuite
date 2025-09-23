"""Application session state and helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum

from server.models import CanonicalSpectrum


class XAxisUnit(str, Enum):
    """Supported wavelength display units."""

    NM = "nm"
    ANGSTROM = "angstrom"
    MICRON = "micron"
    WAVENUMBER = "wavenumber"


class DisplayMode(str, Enum):
    """Supported y-axis display modes."""

    FLUX_DENSITY = "flux_density"
    TRANSMISSION = "transmission"
    ABSORBANCE = "absorbance"
    OPTICAL_DEPTH = "optical_depth"
    RELATIVE_INTENSITY = "relative_intensity"


@dataclass(slots=True)
class TraceView:
    """Visibility and organization metadata for a trace."""

    trace_id: str
    is_visible: bool = True
    is_pinned: bool = False
    is_derived: bool = False


@dataclass(slots=True)
class AppSessionState:
    """Session-scoped state stored inside Streamlit's session_state."""

    traces: dict[str, CanonicalSpectrum] = field(default_factory=dict)
    trace_views: dict[str, TraceView] = field(default_factory=dict)
    trace_order: list[str] = field(default_factory=list)
    x_axis_unit: XAxisUnit = XAxisUnit.NM
    display_mode: DisplayMode = DisplayMode.FLUX_DENSITY
    duplicate_scope: str = "session"
    ingest_ledger: set[tuple[str | None, str]] = field(default_factory=set)

    def register_trace(
        self, trace: CanonicalSpectrum, *, allow_duplicates: bool = False, is_derived: bool = False
    ) -> tuple[bool, str]:
        """Add a trace if it is not a duplicate. Returns (added?, trace_id)."""

        signature = (trace.source_hash, trace.metadata.product_id or trace.label)
        if not allow_duplicates and signature in self.ingest_ledger:
            existing_id = self._find_trace_by_signature(signature)
            return False, existing_id or trace.label

        trace_id = self._next_trace_id(trace.label)
        self.traces[trace_id] = trace
        self.trace_views[trace_id] = TraceView(trace_id=trace_id, is_derived=is_derived)
        self.trace_order.append(trace_id)
        self.ingest_ledger.add(signature)
        return True, trace_id

    def _find_trace_by_signature(self, signature: tuple[str | None, str]) -> str | None:
        for trace_id, trace in self.traces.items():
            candidate = (trace.source_hash, trace.metadata.product_id or trace.label)
            if candidate == signature:
                return trace_id
        return None

    def _next_trace_id(self, label: str) -> str:
        base = label.replace(" ", "_").lower() or "trace"
        candidate = base
        suffix = 1
        while candidate in self.traces:
            suffix += 1
            candidate = f"{base}_{suffix}"
        return candidate

    def visible_traces(self) -> list[CanonicalSpectrum]:
        ordered: list[CanonicalSpectrum] = []
        for trace_id in self.trace_order:
            view = self.trace_views.get(trace_id)
            if view and view.is_visible:
                ordered.append(self.traces[trace_id])
        return ordered

    def toggle_visibility(self, trace_id: str, visible: bool) -> None:
        if trace_id in self.trace_views:
            self.trace_views[trace_id].is_visible = visible

    def remove_trace(self, trace_id: str) -> None:
        if trace_id in self.traces:
            trace = self.traces[trace_id]
            signature = (trace.source_hash, trace.metadata.product_id or trace.label)
            self.ingest_ledger.discard(signature)
            del self.traces[trace_id]
            self.trace_order = [tid for tid in self.trace_order if tid != trace_id]
            self.trace_views.pop(trace_id, None)

    def set_axis_unit(self, unit: XAxisUnit) -> None:
        self.x_axis_unit = unit

    def set_display_mode(self, mode: DisplayMode) -> None:
        self.display_mode = mode

    def iter_traces(self) -> Iterable[tuple[str, CanonicalSpectrum]]:
        for trace_id in self.trace_order:
            yield trace_id, self.traces[trace_id]


SESSION_STATE_KEY = "spectra_app_session"


def get_session_state(st_module, *, default: AppSessionState | None = None) -> AppSessionState:
    """Retrieve or initialize the session state from Streamlit."""

    if SESSION_STATE_KEY not in st_module.session_state:
        st_module.session_state[SESSION_STATE_KEY] = default or AppSessionState()
    return st_module.session_state[SESSION_STATE_KEY]


def reset_session_state(st_module) -> None:
    st_module.session_state.pop(SESSION_STATE_KEY, None)


__all__ = [
    "AppSessionState",
    "DisplayMode",
    "SESSION_STATE_KEY",
    "TraceView",
    "XAxisUnit",
    "get_session_state",
    "reset_session_state",
]
