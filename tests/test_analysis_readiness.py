"""Unit tests for ECAS unified analysis readiness engine."""
import math
from pathlib import Path
import pytest
import numpy as np

from ecas.analysis.readiness import (
    ReadinessIssue,
    ReadinessReport,
    ReadinessStatus,
    evaluate_readiness,
)
from ecas.comparison.eligibility import ComparisonInput
from ecas.comparison.model_generator import get_planet_preset, PLANET_PRESETS
from ecas.identification.library import ReferenceDataset
from ecas.models.spectrum import SpectrumData
from ecas.observations import ObservationContext


def _make_spectrum(
    *,
    wavelengths=(1.0, 2.0, 3.0),
    signals=(0.01, 0.02, 0.015),
    uncertainties=None,
    axis_unit="microns",
    signal_unit="percent",
    signal_type="Transmission",
    source_file="test_obs.csv",
    source_sha256="a" * 64,
):
    cols = ["wavelength", "signal"]
    uncs = uncertainties if uncertainties is not None else tuple([0.001] * len(wavelengths))
    if uncs is not None:
        cols.append("uncertainty")
    rows = []
    for i in range(len(wavelengths)):
        row = {"wavelength": wavelengths[i], "signal": signals[i]}
        if uncs is not None:
            row["uncertainty"] = uncs[i]
        rows.append(row)
    return SpectrumData(
        source_file=Path(source_file),
        rows=tuple(rows),
        columns=tuple(cols),
        axis_unit=axis_unit,
        signal_unit=signal_unit,
        signal_type=signal_type,
    )


class TestAnalysisReadiness:
    def test_view_ready(self):
        spec = _make_spectrum()
        report = evaluate_readiness("view", spec, source_sha256="a" * 64)
        assert report.status == ReadinessStatus.READY
        assert report.is_ready
        assert not report.is_blocked
        assert not report.has_limitations

    def test_view_missing_units_is_ready_with_limitations(self):
        spec = _make_spectrum(axis_unit=None, signal_unit=None)
        report = evaluate_readiness("view", spec, source_sha256="a" * 64)
        assert report.status == ReadinessStatus.READY_WITH_LIMITATIONS
        assert report.has_limitations
        codes = [i.code for i in report.issues]
        assert "view.axis_unit_missing" in codes
        assert "view.signal_unit_missing" in codes

    def test_view_blocked_on_non_positive_or_duplicate_coordinates(self):
        # Non-positive coordinates
        spec_bad = _make_spectrum(wavelengths=(-1.0, 0.0, 1.0))
        report = evaluate_readiness("view", spec_bad)
        assert report.status == ReadinessStatus.BLOCKED
        assert any(i.code == "spectrum.non_positive_coordinates" for i in report.issues)

        # Duplicate coordinates
        spec_dup = _make_spectrum(wavelengths=(1.0, 2.0, 2.0))
        report_dup = evaluate_readiness("view", spec_dup)
        assert report_dup.status == ReadinessStatus.BLOCKED
        assert any(i.code == "spectrum.duplicate_coordinates" for i in report_dup.issues)

    def test_laboratory_fit_blocks_transit_depth(self):
        spec = _make_spectrum(signal_type="Transmission", signal_unit="percent")
        report = evaluate_readiness("laboratory_fit", spec)
        assert report.status == ReadinessStatus.BLOCKED
        issue = next(i for i in report.issues if i.code == "lab.transit_depth_blocked")
        assert "radiative transfer" in issue.consequence
        assert issue.action == "Switch to the Atmospheric Comparison / Forward Model workflow."

    def test_laboratory_fit_requires_references_and_attestation(self):
        spec = _make_spectrum(
            wavelengths=(1000.0, 1500.0, 2000.0),
            signals=(0.1, 0.2, 0.3),
            axis_unit="cm^-1",
            signal_unit="AU",
            signal_type="absorbance",
        )
        from ecas.observations import observation_context
        ctx = observation_context(spec, label="Lab Sample 1")
        report = evaluate_readiness("laboratory_fit", ctx, references=[])
        assert report.status == ReadinessStatus.BLOCKED
        codes = [i.code for i in report.issues]
        assert "lab.metadata.modality_missing" in codes
        assert "lab.references_missing" in codes

    def test_atmospheric_retrieval_ready_with_limitations(self):
        spec = _make_spectrum(
            wavelengths=(1.1, 1.2, 1.3, 1.4, 1.5),
            signals=(2.1, 2.12, 2.11, 2.15, 2.14),
            axis_unit="microns",
            signal_unit="percent",
            signal_type="Transmission",
        )
        preset = get_planet_preset("wasp-39b")
        config = {
            "temperature_k": 1166.0,
            "opacity_sources": [{"formula": "H2O", "dataset": "POKAZATEL"}],
        }
        report = evaluate_readiness(
            "atmospheric_retrieval",
            spec,
            planet_preset=preset,
            forward_model_config=config,
            source_sha256="a" * 64,
        )
        assert report.status == ReadinessStatus.READY_WITH_LIMITATIONS
        assert report.has_limitations
        codes = [i.code for i in report.issues]
        assert "atmos.isothermal_1d_limitation" in codes
        assert "atmos.zero_pressure_broadening_limitation" in codes

    def test_atmospheric_retrieval_blocks_wrong_axis_unit_or_unphysical_preset(self):
        spec = _make_spectrum(axis_unit="nm", signal_unit="percent", signal_type="Transmission")
        preset = get_planet_preset("wasp-39b")
        report = evaluate_readiness("atmospheric_retrieval", spec, planet_preset=preset)
        assert report.status == ReadinessStatus.BLOCKED
        assert any(i.code == "atmos.axis_unit_not_microns" for i in report.issues)

    def test_report_serialization(self):
        spec = _make_spectrum()
        report = evaluate_readiness("view", spec, source_sha256="a" * 64)
        data = report.to_dict()
        assert data["status"] == "Ready"
        assert data["operation"] == "view"
        assert len(report.summary_lines()) >= 1
