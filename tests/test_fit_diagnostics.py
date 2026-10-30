"""Unit tests for fit and retrieval diagnostics."""
import numpy as np
import pytest

from ecas.comparison.diagnostics import (
    ComprehensiveFitDiagnostics,
    ResidualStructureDiagnostics,
    compute_comprehensive_fit_diagnostics,
    compute_residual_structure_diagnostics,
)


class TestFitDiagnostics:
    def test_random_residuals_pass_runs_test_and_autocorrelation(self):
        np.random.seed(42)
        res = np.random.normal(0, 1, 100)
        unc = np.ones(100)

        diag = compute_residual_structure_diagnostics(res, uncertainties=unc, parameter_count=2)
        assert diag.sample_count == 100
        assert diag.degrees_of_freedom == 98
        assert diag.reduced_chi2 == pytest.approx(1.0, rel=0.25)
        # Random residuals should not fail runs test
        assert diag.runs_z_score is not None
        assert abs(diag.runs_z_score) < 1.96
        assert "Random residual sign" in diag.runs_interpretation
        assert abs(diag.lag1_autocorrelation) < 0.25

    def test_systematic_residuals_trigger_runs_clustering(self):
        # 50 positive followed by 50 negative residuals (2 runs total)
        res = np.concatenate([np.ones(50), -np.ones(50)])
        unc = np.ones(100)

        diag = compute_residual_structure_diagnostics(res, uncertainties=unc)
        assert diag.runs_count == 2
        assert diag.runs_z_score is not None
        assert diag.runs_z_score < -1.96
        assert "Negative run clustering" in diag.runs_interpretation
        assert diag.lag1_autocorrelation > 0.50

    def test_ill_conditioned_covariance_detection(self):
        res = np.array([0.1, -0.1, 0.05, -0.05])
        # Near singular covariance
        cov = np.array([
            [1.0, 1.0 - 1e-14, 0.0, 0.0],
            [1.0 - 1e-14, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])

        diag = compute_residual_structure_diagnostics(res, covariance=cov)
        assert diag.ill_conditioned
        assert diag.condition_number > 1e12

    def test_comprehensive_fit_diagnostics_progressive_disclosure(self):
        res = [0.01, -0.02, 0.015, -0.01, 0.005]
        unc = [0.01] * 5

        comp = compute_comprehensive_fit_diagnostics(
            "Test Fit",
            res,
            uncertainties=unc,
            parameter_count=1,
            solver_name="scipy.optimize.lsq_linear",
            converged=True,
            parameters_at_bounds=["VMR_CH4"],
        )

        assert isinstance(comp, ComprehensiveFitDiagnostics)
        assert "Boundary Alert" in comp.plain_language_summary
        assert "VMR_CH4" in comp.solver_status.parameters_at_bounds
        assert len(comp.progressive_disclosure_math) >= 4
        assert "χ²_ν" in comp.progressive_disclosure_math["Reduced Chi-Squared"]
        assert "Awaiting MCMC / Nested-Sampling" in comp.retrieval_backend_contract["status"]
        assert "must NEVER be transformed into Bayesian posteriors" in comp.retrieval_backend_contract["boundary_warning"]

        d = comp.to_dict()
        assert d["fit_name"] == "Test Fit"
        assert "solver_status" in d
        assert "residual_structure" in d

