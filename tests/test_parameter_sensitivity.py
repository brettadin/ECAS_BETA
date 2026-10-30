"""Unit tests for parameter sensitivity and observational constraints."""
from pathlib import Path
import numpy as np
import pytest

from ecas.comparison.model_generator import build_illustrative_band_component, get_planet_preset
from ecas.comparison.sensitivity import (
    SCIENTIFIC_BOUNDARY_NOTICE,
    SensitivityAnalysisResult,
    compute_parameter_sensitivity,
)
from ecas.models.spectrum import SpectrumData


def _make_wasp39b_spectrum(*, with_uncertainties=True):
    # Mock observation over 2.0 to 5.0 microns (WASP-39 b NIRSpec band)
    w = np.linspace(2.0, 5.0, 60)
    # Transit depth ~ 2.1%
    d = 2.10 + 0.04 * np.sin(2 * np.pi * (w - 2.0) / 1.5)
    unc = 0.01 * np.ones_like(w) if with_uncertainties else None

    cols = ["wavelength", "signal"]
    if with_uncertainties:
        cols.append("uncertainty")
    rows = []
    for i in range(len(w)):
        r = {"wavelength": float(w[i]), "signal": float(d[i])}
        if with_uncertainties:
            r["uncertainty"] = float(unc[i])
        rows.append(r)
    return SpectrumData(
        source_file=Path("wasp39b_mock_obs.csv"),
        rows=tuple(rows),
        columns=tuple(cols),
        axis_unit="microns",
        signal_unit="percent",
        signal_type="Transmission",
    )


class TestParameterSensitivity:
    def test_sensitivity_with_uncertainties(self):
        spec = _make_wasp39b_spectrum(with_uncertainties=True)
        h2o = build_illustrative_band_component("H2O", 1.0e-3, wavelength_min_um=1.8, wavelength_max_um=5.2)
        co2 = build_illustrative_band_component("CO2", 1.0e-4, wavelength_min_um=1.8, wavelength_max_um=5.2)

        res = compute_parameter_sensitivity(
            spec,
            planet_preset_id="wasp-39b",
            components=[h2o, co2],
            delta_temp_k=50.0,
            delta_radius_fraction=0.02,
        )

        assert isinstance(res, SensitivityAnalysisResult)
        assert len(res.wavelengths_um) == 60
        assert res.uncertainty_kind == "observational_1sigma"
        assert res.uncertainties is not None
        assert len(res.perturbations) >= 8  # T (+/-), Rp (+/-), Pcloud (+/-), H2O (+/-), CO2 (+/-)

        # Check temperature perturbation
        t_plus = next(p for p in res.perturbations if p.parameter_name == "temperature_k" and p.perturbation_direction == "+")
        assert t_plus.baseline_value == 1166.0
        assert t_plus.perturbed_value == 1216.0
        assert t_plus.relative_to_uncertainty is not None
        assert len(t_plus.delta_spectrum) == 60
        assert t_plus.max_abs_delta > 0.0

        # Check that scientific boundary notice is present
        assert "NOT a posterior probability" in res.scientific_boundary_notice

    def test_sensitivity_unweighted_mode(self):
        spec = _make_wasp39b_spectrum(with_uncertainties=False)
        h2o = build_illustrative_band_component("H2O", 1.0e-3, wavelength_min_um=1.8, wavelength_max_um=5.2)

        res = compute_parameter_sensitivity(
            spec,
            planet_preset_id="wasp-39b",
            components=[h2o],
        )

        assert res.uncertainty_kind == "unweighted"
        assert res.uncertainties is None
        assert any("no positive 1-sigma uncertainty" in w for w in res.warnings)

        for p in res.perturbations:
            assert p.relative_to_uncertainty is None

    def test_degeneracy_detection(self):
        spec = _make_wasp39b_spectrum(with_uncertainties=True)
        h2o = build_illustrative_band_component("H2O", 1.0e-3, wavelength_min_um=1.8, wavelength_max_um=5.2)

        res = compute_parameter_sensitivity(
            spec,
            planet_preset_id="wasp-39b",
            components=[h2o],
        )

        assert len(res.degeneracies) > 0
        # Check that each degeneracy object has valid correlations
        for d in res.degeneracies:
            assert -1.0 <= d.correlation_coefficient <= 1.0
            assert isinstance(d.is_degenerate, bool)
            assert len(d.explanation) > 0

    def test_serialization(self):
        spec = _make_wasp39b_spectrum(with_uncertainties=True)
        res = compute_parameter_sensitivity(spec, planet_preset_id="wasp-39b")
        d = res.to_dict()
        assert d["target_id"] == "wasp39b_mock_obs.csv"
        assert len(d["perturbations"]) > 0
        assert "baseline_parameters" in d

