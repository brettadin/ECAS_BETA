"""Unit tests for multi-observation consistency and reduction comparison."""
from pathlib import Path
import numpy as np
import pytest

from ecas.comparison.consistency import (
    MultiObservationConsistencyReport,
    compare_observation_consistency,
)
from ecas.models.spectrum import SpectrumData
from ecas.observations import observation_context


def _make_reduction_spectrum(name, *, offset=0.0, noise_level=0.005, w_range=(2.0, 5.0), n_pts=60):
    w = np.linspace(w_range[0], w_range[1], n_pts)
    signal = 2.10 + offset + 0.03 * np.sin(2 * np.pi * (w - 2.0) / 1.5)
    unc = noise_level * np.ones_like(w)
    rows = [
        {"wavelength": float(w[i]), "signal": float(signal[i]), "uncertainty": float(unc[i])}
        for i in range(len(w))
    ]
    return SpectrumData(
        source_file=Path(name),
        rows=tuple(rows),
        columns=("wavelength", "signal", "uncertainty"),
        axis_unit="microns",
        signal_unit="percent",
        signal_type="Transmission",
    )


class TestObservationConsistency:
    def test_duplicate_file_detection(self):
        spec1 = _make_reduction_spectrum("wasp39b_eureka.csv")
        ctx1 = observation_context(spec1, source_sha256="b" * 64, label="Eureka Red 1")
        ctx2 = observation_context(spec1, source_sha256="b" * 64, label="Eureka Copy")

        report = compare_observation_consistency([ctx1, ctx2])
        assert report.has_duplicate_files
        pair = report.pairwise_comparisons[0]
        assert pair.relationship == "DUPLICATE_FILE"
        assert "duplicate files" in (pair.independence_warning or "")

    def test_alternative_reduction_clustering(self):
        spec_eureka = _make_reduction_spectrum("Eureka_transit_spec.csv", offset=0.0)
        spec_firefly = _make_reduction_spectrum("FIREFLy_transit_spec.csv", offset=0.02)
        spec_tiberius = _make_reduction_spectrum("Tiberius_transit_spec.csv", offset=-0.01)

        ctx_eur = observation_context(spec_eureka, source_sha256="1" * 64, label="Eureka")
        ctx_fir = observation_context(spec_firefly, source_sha256="2" * 64, label="FIREFLy")
        ctx_tib = observation_context(spec_tiberius, source_sha256="3" * 64, label="Tiberius")

        report = compare_observation_consistency([ctx_eur, ctx_fir, ctx_tib])
        assert len(report.alternative_reduction_clusters) == 1
        assert len(report.alternative_reduction_clusters[0]) == 3

        # All pairs must be classified as ALTERNATIVE_REDUCTION
        for pair in report.pairwise_comparisons:
            assert pair.relationship == "ALTERNATIVE_REDUCTION"
            assert "alternative reduction pipelines" in (pair.independence_warning or "")
            assert pair.overlap_range_um == (2.0, 5.0)
            assert pair.resolution_compatible

            # Systematic offset accurately computed
            assert pair.systematic_median_offset is not None
            assert pair.offset_subtracted_rms is not None
            assert pair.nuisance_parameter_spec is not None
            assert "offset_" in pair.nuisance_parameter_spec["parameter_name"]

    def test_disjoint_coverage_insufficient_overlap(self):
        spec1 = _make_reduction_spectrum("band1.csv", w_range=(1.0, 2.0))
        spec2 = _make_reduction_spectrum("band2.csv", w_range=(3.0, 4.0))

        report = compare_observation_consistency([spec1, spec2])
        pair = report.pairwise_comparisons[0]
        assert pair.overlap_range_um is None
        assert not pair.resolution_compatible
        assert pair.systematic_median_offset is None
        assert "Disjoint wavelength coverage" in pair.resolution_notes

    def test_report_serialization(self):
        spec1 = _make_reduction_spectrum("Eureka_transit_spec.csv", offset=0.0)
        spec2 = _make_reduction_spectrum("FIREFLy_transit_spec.csv", offset=0.01)

        report = compare_observation_consistency([spec1, spec2])
        d = report.to_dict()
        assert len(d["datasets"]) == 2
        assert len(d["pairwise_comparisons"]) == 1
        assert "target_name" in d

