"""Fit and retrieval diagnostics with progressive disclosure.

Evaluates mathematical and statistical diagnostics for existing fits:
- Solver convergence and parameter bounds clamping.
- Residual structure: reduced chi-squared, Wald-Wolfowitz runs test for randomness,
  lag-1 autocorrelation for correlated noise, and normality checks.
- Matrix condition number kappa(C).
- Uncertainty dependence (supplied 1-sigma vs estimated noise).

Documents the formal specification for downstream posterior retrieval backends
(nested sampling, priors, Gelman-Rubin convergence, credible intervals, KL divergence)
while strictly forbidding false conversion of conditional fit scores into Bayesian posteriors.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Sequence

import numpy as np


@dataclass(frozen=True)
class ResidualStructureDiagnostics:
    """Statistical diagnostics of fit residuals to assess model adequacy and correlated noise."""

    sample_count: int
    parameter_count: int
    degrees_of_freedom: int
    raw_rms: float
    mean_residual: float
    chi2: float | None
    reduced_chi2: float | None
    runs_count: int
    positive_count: int
    negative_count: int
    runs_z_score: float | None
    runs_interpretation: str
    lag1_autocorrelation: float
    autocorrelation_interpretation: str
    skewness: float
    kurtosis: float
    condition_number: float | None
    ill_conditioned: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SolverStatusDiagnostics:
    """Convergence and boundary diagnostics for optimization solvers."""

    solver_name: str
    converged: bool
    iterations: int | None
    message: str
    parameters_at_bounds: tuple[str, ...]
    uncertainty_basis: str  # 'supplied_1sigma', 'supplied_covariance', 'estimated_residual_variance', 'unweighted'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComprehensiveFitDiagnostics:
    """Complete diagnostic suite combining solver status, residual statistics, and math disclosures."""

    fit_name: str
    solver_status: SolverStatusDiagnostics
    residual_structure: ResidualStructureDiagnostics
    plain_language_summary: str
    progressive_disclosure_math: dict[str, str]
    retrieval_backend_status: str
    retrieval_backend_contract: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fit_name": self.fit_name,
            "solver_status": self.solver_status.to_dict(),
            "residual_structure": self.residual_structure.to_dict(),
            "plain_language_summary": self.plain_language_summary,
            "progressive_disclosure_math": self.progressive_disclosure_math,
            "retrieval_backend_status": self.retrieval_backend_status,
            "retrieval_backend_contract": self.retrieval_backend_contract,
        }


def compute_residual_structure_diagnostics(
    residuals: Sequence[float],
    *,
    uncertainties: Sequence[float] | None = None,
    parameter_count: int = 1,
    covariance: Sequence[Sequence[float]] | np.ndarray | None = None,
) -> ResidualStructureDiagnostics:
    """Compute Wald-Wolfowitz runs test, autocorrelation, reduced chi2, and conditioning."""
    res_arr = np.asarray(residuals, dtype=float)
    n = len(res_arr)
    if n < 3:
        raise ValueError("Residual structure evaluation requires at least 3 samples")

    raw_rms = float(np.sqrt(np.mean(res_arr ** 2)))
    mean_res = float(np.mean(res_arr))
    dof = max(1, n - parameter_count)

    # 1. Chi-squared & Reduced Chi-squared
    chi2: float | None = None
    red_chi2: float | None = None
    if uncertainties is not None:
        sig_arr = np.asarray(uncertainties, dtype=float)
        if len(sig_arr) == n and np.all(sig_arr > 0):
            chi2 = float(np.sum((res_arr / sig_arr) ** 2))
            red_chi2 = float(chi2 / dof)

    # 2. Wald-Wolfowitz Runs Test on Residual Signs
    signs = np.sign(res_arr)
    signs = signs[signs != 0]  # ignore exact zeros
    n_pos = int(np.count_nonzero(signs > 0))
    n_neg = int(np.count_nonzero(signs < 0))

    runs = 1 if len(signs) > 0 else 0
    for i in range(1, len(signs)):
        if signs[i] != signs[i - 1]:
            runs += 1

    runs_z: float | None = None
    runs_interp = "Insufficient non-zero signs for runs test"
    if n_pos > 2 and n_neg > 2:
        n_tot = n_pos + n_neg
        exp_runs = (2.0 * n_pos * n_neg / n_tot) + 1.0
        var_runs = (2.0 * n_pos * n_neg * (2.0 * n_pos * n_neg - n_tot)) / (n_tot ** 2 * (n_tot - 1.0))
        if var_runs > 0:
            runs_z = float((runs - exp_runs) / math.sqrt(var_runs))
            if runs_z < -1.96:
                runs_interp = f"Negative run clustering (Z = {runs_z:.2f} < -1.96); residuals exhibit systematic positive/negative runs indicating unmodeled physical features or baseline shifts."
            elif runs_z > 1.96:
                runs_interp = f"Excessive sign alternation (Z = {runs_z:.2f} > +1.96); residuals oscillate more rapidly than random noise."
            else:
                runs_interp = f"Random residual sign distribution (Z = {runs_z:.2f}); consistent with independent random errors."

    # 3. Lag-1 Autocorrelation (r_1)
    centered = res_arr - mean_res
    denom = np.sum(centered ** 2)
    if denom > 1e-15:
        lag1_corr = float(np.sum(centered[:-1] * centered[1:]) / denom)
    else:
        lag1_corr = 0.0

    if abs(lag1_corr) > 0.30:
        autocorr_interp = (
            f"Significant lag-1 residual autocorrelation (r_1 = {lag1_corr:+.2f}); "
            "indicates correlated noise, detector systematic trends, or missing continuum slope."
        )
    else:
        autocorr_interp = f"Low lag-1 autocorrelation (r_1 = {lag1_corr:+.2f}); residuals appear largely uncorrelated."

    # 4. Standardized residual moments (skewness and kurtosis)
    if raw_rms > 1e-15:
        norm_res = centered / raw_rms
        skew = float(np.mean(norm_res ** 3))
        kurt = float(np.mean(norm_res ** 4) - 3.0)  # excess kurtosis
    else:
        skew = 0.0
        kurt = 0.0

    # 5. Covariance conditioning
    cond_num: float | None = None
    ill_cond = False
    if covariance is not None:
        cov_mat = np.asarray(covariance, dtype=float)
        if cov_mat.ndim == 2 and cov_mat.shape[0] == cov_mat.shape[1]:
            try:
                cond_num = float(np.linalg.cond(cov_mat))
                ill_cond = cond_num > 1e12
            except np.linalg.LinAlgError:
                cond_num = float("inf")
                ill_cond = True

    return ResidualStructureDiagnostics(
        sample_count=n,
        parameter_count=parameter_count,
        degrees_of_freedom=dof,
        raw_rms=raw_rms,
        mean_residual=mean_res,
        chi2=chi2,
        reduced_chi2=red_chi2,
        runs_count=runs,
        positive_count=n_pos,
        negative_count=n_neg,
        runs_z_score=runs_z,
        runs_interpretation=runs_interp,
        lag1_autocorrelation=lag1_corr,
        autocorrelation_interpretation=autocorr_interp,
        skewness=skew,
        kurtosis=kurt,
        condition_number=cond_num,
        ill_conditioned=ill_cond,
    )


def compute_comprehensive_fit_diagnostics(
    fit_name: str,
    residuals: Sequence[float],
    *,
    uncertainties: Sequence[float] | None = None,
    parameter_count: int = 1,
    covariance: Sequence[Sequence[float]] | np.ndarray | None = None,
    solver_name: str = "Bounded-Variable Least Squares (BVLS)",
    converged: bool = True,
    iterations: int | None = None,
    solver_message: str = "Optimization terminated successfully",
    parameters_at_bounds: Sequence[str] = (),
    uncertainty_basis: str | None = None,
) -> ComprehensiveFitDiagnostics:
    """Generate complete fit diagnostics with plain-language summary and progressive disclosure."""
    res_struct = compute_residual_structure_diagnostics(
        residuals,
        uncertainties=uncertainties,
        parameter_count=parameter_count,
        covariance=covariance,
    )

    resolved_basis = uncertainty_basis or (
        "supplied_covariance" if covariance is not None else
        "supplied_1sigma" if uncertainties is not None else
        "unweighted"
    )

    solver_status = SolverStatusDiagnostics(
        solver_name=solver_name,
        converged=converged,
        iterations=iterations,
        message=solver_message,
        parameters_at_bounds=tuple(parameters_at_bounds),
        uncertainty_basis=resolved_basis,
    )

    # Build plain language summary
    summary_parts = []
    if not converged:
        summary_parts.append(f"Solver Warning: {solver_name} did NOT converge ({solver_message}).")
    elif parameters_at_bounds:
        summary_parts.append(f"Boundary Alert: Parameter(s) [{', '.join(parameters_at_bounds)}] hit physical boundaries.")
    else:
        summary_parts.append("Optimization solver converged normally without hitting parameter boundaries.")

    if res_struct.reduced_chi2 is not None:
        if 0.8 <= res_struct.reduced_chi2 <= 1.5:
            summary_parts.append(f"Goodness-of-fit is statistically consistent with 1σ errors (χ_ν² = {res_struct.reduced_chi2:.2f}).")
        elif res_struct.reduced_chi2 > 2.0:
            summary_parts.append(f"Elevated residual variance (χ_ν² = {res_struct.reduced_chi2:.2f} >> 1.0); model underfits or errors are underestimated.")
        else:
            summary_parts.append(f"Low residual variance (χ_ν² = {res_struct.reduced_chi2:.2f} << 1.0); potential error overestimation.")
    else:
        summary_parts.append("Goodness-of-fit evaluated with unweighted residual RMS; no observation error column was supplied.")

    summary_parts.append(res_struct.runs_interpretation)
    if abs(res_struct.lag1_autocorrelation) > 0.30:
        summary_parts.append(res_struct.autocorrelation_interpretation)

    summary_text = " ".join(summary_parts)

    math_disclosures = {
        "Reduced Chi-Squared (χ²_ν)": (
            "χ²_ν = [1 / (N − k)] · Σ [ (y_i − f(x_i)) / σ_i ]²\n"
            "Where N is the number of valid observed points, k is the number of fitted parameters, "
            "and degrees of freedom ν = N − k. Evaluates goodness of fit per degree of freedom (1.0 indicates consistency with 1σ errors)."
        ),
        "Reduced Chi-Squared": (
            "χ²_ν = [1 / (N − k)] · Σ [ (y_i − f(x_i)) / σ_i ]²\n"
            "Where N is the number of valid observed points, k is the number of fitted parameters, "
            "and degrees of freedom ν = N − k. Evaluates goodness of fit per degree of freedom (1.0 indicates consistency with 1σ errors)."
        ),
        "Wald-Wolfowitz Runs Test (Z)": (
            "Z = [ R − ( (2·n₊·n₋ / N) + 1 ) ] / σ_R\n"
            "Where R is the total number of runs, n₊ and n₋ are positive and negative residual counts, "
            "and σ_R = √[ (2·n₊·n₋ · (2·n₊·n₋ − N)) / (N² · (N − 1)) ]. "
            "Tests whether residuals fluctuate randomly around the model or cluster into systematic trends."
        ),
        "Lag-1 Residual Autocorrelation (r₁)": (
            "r₁ = [ Σ (r_i − r̄)·(r_i₊₁ − r̄) ] / [ Σ (r_i − r̄)² ]\n"
            "Measures point-to-point residual correlation. Values near 0 indicate independent white noise; "
            "values > 0.3 flag correlated red noise or unmodeled molecular absorption features."
        ),
        "Covariance Condition Number (κ)": (
            "κ(C) = ‖C‖₂ · ‖C⁻¹‖₂ = λ_max(C) / λ_min(C)\n"
            "Ratio of the largest to smallest eigenvalue of the parameter covariance matrix. "
            "Values > 10¹² indicate ill-conditioned, numerically degenerate parameter combinations."
        ),
    }

    retrieval_contract = {
        "status": "Awaiting MCMC / Nested-Sampling Retrieval Backend",
        "required_backend_methods": [
            "define_parameter_priors(priors: dict[str, PriorDistribution])",
            "log_likelihood(params: dict[str, float], observation: ComparisonInput) -> float",
            "run_nested_sampling(nlive: int, tolerance: float) -> RetrievalPosteriorResult",
        ],
        "required_posterior_diagnostics": [
            "marginalized_credible_intervals (16th, 50th, 84th percentiles)",
            "gelman_rubin_r_hat (MCMC convergence, requirement R_hat < 1.05)",
            "effective_sample_size_n_eff (autocorrelation length integration)",
            "kullback_leibler_divergence (information gain D_KL(P || Pi) over prior)",
            "corner_plot_parameter_correlations",
        ],
        "boundary_warning": (
            "ECAS currently uses deterministic forward-model residuals and bounded least-squares fits. "
            "Conditional Delta-chi2 or BVLS scores must NEVER be transformed into Bayesian posteriors "
            "or detection probabilities without a verified sampling engine."
        ),
    }

    return ComprehensiveFitDiagnostics(
        fit_name=fit_name,
        solver_status=solver_status,
        residual_structure=res_struct,
        plain_language_summary=summary_text,
        progressive_disclosure_math=math_disclosures,
        retrieval_backend_status="Deterministic Forward Model Diagnostics Active (Posterior Sampler Contract Documented)",
        retrieval_backend_contract=retrieval_contract,
    )

