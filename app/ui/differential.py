"""Differential tab UI."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import streamlit as st

from app.state.session import AppSessionState
from server.math.differential import DifferentialProduct, divide, subtract
from server.models import CanonicalSpectrum, ProvenanceEvent


@dataclass(slots=True)
class DifferentialSettings:
    epsilon: float = 1e-8


def _add_trace(session: AppSessionState, product: DifferentialProduct, *, epsilon: float) -> None:
    spectrum = product.spectrum
    spectrum.provenance.append(
        ProvenanceEvent(
            step="differential_ui_add",
            parameters={"epsilon": epsilon, "operation": product.operation},
        )
    )
    session.register_trace(spectrum, allow_duplicates=True, is_derived=True)


def _add_trivial_trace(session: AppSessionState, base: CanonicalSpectrum, label: str) -> None:
    zeros = np.zeros_like(base.values)
    spectrum = CanonicalSpectrum(
        label=label,
        wavelength_vac_nm=base.wavelength_vac_nm,
        values=zeros,
        value_mode=base.value_mode,
        value_unit=base.value_unit,
        metadata=base.metadata,
        provenance=base.provenance + [ProvenanceEvent(step="differential_trivial", parameters={})],
        source_hash=None,
        uncertainties=np.zeros_like(base.values) if base.uncertainties is not None else None,
    )
    session.register_trace(spectrum, allow_duplicates=True, is_derived=True)


def render_differential_tab(
    session: AppSessionState, settings: DifferentialSettings | None = None
) -> None:
    settings = settings or DifferentialSettings()
    st.subheader("Differential Analysis")

    if len(session.trace_order) < 2:
        st.info("Add at least two traces to compute differentials.")
        return

    def _format(trace_id: str) -> str:
        return session.traces[trace_id].label

    a_id = st.selectbox("Trace A", session.trace_order, format_func=_format)
    b_id = st.selectbox(
        "Trace B",
        session.trace_order,
        index=min(1, len(session.trace_order) - 1),
        format_func=_format,
    )

    trace_a = session.traces[a_id]
    trace_b = session.traces[b_id]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Compute A - B"):
            product = subtract(trace_a, trace_b, epsilon=settings.epsilon)
            if product is None:
                st.warning("Traces are numerically identical; difference suppressed.")
                if st.button("Add zero difference anyway", key="add_diff_anyway"):
                    _add_trivial_trace(session, trace_a, f"{trace_a.label}-{trace_b.label}")
            else:
                _add_trace(session, product, epsilon=settings.epsilon)
                st.success(f"Added differential trace {product.spectrum.label}")
    with col2:
        if st.button("Compute A / B"):
            product = divide(trace_a, trace_b, epsilon=settings.epsilon)
            if product is None:
                st.warning("Traces are numerically identical; ratio suppressed.")
                if st.button("Add unity ratio anyway", key="add_ratio_anyway"):
                    unity = CanonicalSpectrum(
                        label=f"{trace_a.label}/{trace_b.label}",
                        wavelength_vac_nm=trace_a.wavelength_vac_nm,
                        values=np.ones_like(trace_a.values),
                        value_mode="relative_intensity",
                        value_unit=None,
                        metadata=trace_a.metadata,
                        provenance=trace_a.provenance
                        + [ProvenanceEvent(step="differential_trivial", parameters={})],
                        source_hash=None,
                        uncertainties=None,
                    )
                    session.register_trace(unity, allow_duplicates=True, is_derived=True)
            else:
                _add_trace(session, product, epsilon=settings.epsilon)
                st.success(f"Added differential trace {product.spectrum.label}")

    st.caption("Differentials respect flux-conserving resampling with ε-stabilized ratios.")
