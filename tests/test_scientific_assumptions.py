"""Unit tests for scientific assumption comparison."""
import pytest
from ecas.comparison.assumptions import (
    BAYESIAN_EVIDENCE_NOTICE,
    DOMAIN_MISMATCH_WARNING,
    AssumptionsManager,
    ScientificAssumptionVariant,
    compare_scientific_assumptions,
)


def _make_variant(
    name,
    *,
    config_id="c1",
    atmosphere="cloudy",
    cloud_p=0.01,
    opacity="real_exomol",
    species=("H2O", "CO2"),
    w_range=(1.0, 5.0),
    n_pts=50,
    rms=0.02,
    chi2=1.2,
):
    preds = tuple([2.10] * n_pts)
    resids = tuple([0.01] * n_pts)
    indices = tuple(range(n_pts))
    return ScientificAssumptionVariant(
        config_id=config_id,
        name=name,
        target_id="WASP-39 b",
        atmosphere_structure=atmosphere,
        cloud_pressure_bar=cloud_p,
        opacity_source_kind=opacity,
        included_species=species,
        wavelength_range_um=w_range,
        data_point_count=n_pts,
        data_indices=indices,
        noise_treatment="independent_gaussian_1sigma",
        model_predictions=preds,
        residuals=resids,
        rms_residual=rms,
        reduced_chi2=chi2,
        limitations=("1D isothermal assumption",),
    )


class TestScientificAssumptions:
    def test_compare_identical_domains(self):
        v_cloudy = _make_variant("Cloudy Baseline", config_id="c1", atmosphere="cloudy", cloud_p=0.01, rms=0.02, chi2=1.2)
        v_clear = _make_variant("Clear Atmosphere", config_id="c2", atmosphere="clear", cloud_p=None, rms=0.035, chi2=2.1)

        delta = compare_scientific_assumptions(v_cloudy, v_clear)
        assert delta.data_domains_identical
        assert delta.domain_warning is None
        assert any("Atmosphere Structure" in diff for diff in delta.assumption_differences)
        assert delta.delta_reduced_chi2 == pytest.approx(0.9)
        assert delta.delta_rms_residual == pytest.approx(0.015)
        assert not delta.evidence_comparison_available
        assert "Bayesian evidence" in delta.evidence_statement

    def test_compare_different_wavelength_domains_blocks_chi2_ranking(self):
        v_full = _make_variant("Full PRISM (1.0-5.0 um)", config_id="c1", w_range=(1.0, 5.0), n_pts=60, chi2=1.2)
        v_sub = _make_variant("Sub-band (3.0-5.0 um)", config_id="c2", w_range=(3.0, 5.0), n_pts=30, chi2=0.8)

        delta = compare_scientific_assumptions(v_full, v_sub)
        assert not delta.data_domains_identical
        assert delta.domain_warning == DOMAIN_MISMATCH_WARNING
        # Chi2 comparison must be None to prevent false ranking
        assert delta.delta_reduced_chi2 is None
        assert any("Wavelength Span" in diff for diff in delta.assumption_differences)

    def test_chemistry_differences(self):
        v_full = _make_variant("Full Chemistry", config_id="c1", species=("H2O", "CO2", "SO2"))
        v_drop = _make_variant("No SO2", config_id="c2", species=("H2O", "CO2"))

        delta = compare_scientific_assumptions(v_full, v_drop)
        assert any("omitted SO2" in diff for diff in delta.assumption_differences)

    def test_manager_lifecycle(self):
        mgr = AssumptionsManager()
        v1 = _make_variant("V1", config_id="1")
        v2 = _make_variant("V2", config_id="2")
        mgr.add_variant(v1)
        mgr.add_variant(v2)

        assert len(mgr.list_variants()) == 2
        assert mgr.get_variant("1") == v1
        mgr.clear()
        assert len(mgr.list_variants()) == 0

