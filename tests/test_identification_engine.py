"""Numerical fidelity checked on actual reference measurements.

Self-comparison below is explicitly an algebra/round-trip check; it does not
demonstrate independent scientific identification or detection calibration.
"""
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from ecas.identification.engine import identify, result_to_record, verify_record, reproduce_record
from ecas.identification.library import discover_library

ROOT = Path(__file__).resolve().parents[1] / "data" / "ECAS_Spectral_Library"


@pytest.fixture(scope="module")
def refs():
    return discover_library(ROOT).datasets


def test_real_measurement_self_fit_matches_independent_v1_refit(refs):
    reference = next(r for r in refs if r.molecule == "C2H2" and r.modality == "IR")
    result = identify(reference.spectrum, [reference], observation_metadata=reference.metadata)
    assert result.components[0].status == "evaluated"
    assert result.components[0].amplitude == pytest.approx(1, abs=1e-7)
    nu, tau, sigma = np.asarray(result.x), np.asarray(result.observed), np.asarray(result.sigma_values)
    u = 2 * (nu - nu[0]) / (nu[-1] - nu[0]) - 1
    baseline = np.column_stack((np.ones_like(u), u)) / sigma[:, None]
    fit = np.linalg.lstsq(baseline, tau / sigma, rcond=None)[0]
    without = np.sum((baseline @ fit - tau / sigma) ** 2)
    assert result.components[0].delta_chi2 == pytest.approx(max(without - result.chi2, 0), rel=1e-9)
    assert result.components[0].sigma ** 2 == pytest.approx(result.components[0].delta_chi2)
    assert result.sigma_estimated
    # v1 residual MAD uses a 1e-6 transmittance floor on this exact round trip.
    assert np.asarray(result.sigma_values) == pytest.approx(1e-6 / np.exp(-tau))
    assert any("no calibrated" in s for s in result.warnings)


def test_supplied_uncertainty_preserves_v1_weight_propagation(refs):
    reference = next(r for r in refs if r.molecule == "C2H2" and r.modality == "IR")
    # Error envelope derived from source sampling precision, explicitly a
    # test of the supplied-error branch rather than invented measurements.
    quantization = float(np.min(np.diff(np.unique([r["signal"] for r in reference.spectrum.rows])))) / 2
    obs = replace(reference.spectrum, columns=reference.spectrum.columns + ("uncertainty",),
                  rows=tuple(dict(row, uncertainty=quantization) for row in reference.spectrum.rows))
    result = identify(obs, [reference], observation_metadata=reference.metadata)
    assert not result.sigma_estimated
    assert result.components[0].status == "evaluated"
    assert result.sigma_values == pytest.approx(np.maximum(quantization / np.exp(-np.array(result.observed)), 1e-6))


def test_modality_phase_transit_and_duplicates_are_explicitly_blocked(refs):
    water = next(r for r in refs if r.modality == "IR" and r.molecule == "H2O" and r.metadata["phase"] == "liquid")
    methane_uv = next(r for r in refs if r.modality == "UV-Vis" and r.molecule == "CH4")
    gas = next(r for r in refs if r.modality == "IR" and r.molecule == "H2O" and r.metadata["phase"] == "gas")
    result = identify(gas.spectrum, [water, methane_uv], observation_metadata={"modality": "IR", "phase": "gas"})
    assert "Phase mismatch" in result.components[0].reason
    assert "modality" in result.components[1].reason
    transit = replace(water.spectrum, signal_type="Transmission", signal_unit="%")
    assert "radiative-transfer" in identify(transit, [water]).components[0].reason
    ph3 = next(r for r in refs if r.modality == "UV-Vis" and r.molecule == "PH3")
    duplicate = identify(ph3.spectrum, [ph3], observation_metadata={"modality": "UV-Vis"})
    assert duplicate.components[0].sigma is None and "Duplicate" in duplicate.components[0].reason


def test_signed_uv_self_fit_is_exploratory_and_keeps_negative_data(refs):
    reference = next(r for r in refs if r.modality == "UV-Vis" and r.molecule != "PH3"
                     and any(row["signal"] < 0 for row in r.spectrum.rows))
    result = identify(reference.spectrum, [reference], observation_metadata={"modality": "UV-Vis"})
    assert result.components[0].status == "evaluated"
    assert min(result.observed) < 0
    assert result.components[0].amplitude == pytest.approx(1., abs=1e-6)
    assert result.settings["fit_quantity"] == "cross_section"
    assert any("Exploratory signed" in s for s in result.warnings)
    record = result_to_record(result)
    assert verify_record(record)
    repeated = reproduce_record(record)
    assert repeated.components[0].sigma == pytest.approx(result.components[0].sigma)
    assert repeated.model == pytest.approx(result.model)
    record["payload"]["settings"]["threshold"] = 9
    assert not verify_record(record)


def test_real_multiple_candidates_have_individual_rows_and_component_curves(refs):
    methane = [r for r in refs if r.modality == "IR" and r.molecule == "CH4"]
    result = identify(methane[0].spectrum, methane, observation_metadata=methane[0].metadata)
    assert len(result.components) == len(methane)
    assert all(c.status == "evaluated" for c in result.components)
    assert set(result.component_curves) == {r.dataset_id for r in methane}
    assert all(len(curve) == len(result.x) for curve in result.component_curves.values())
    # Independently solve each omitted-column model on the exact same real
    # data/domain/weights. Remaining molecular coefficients are refitted.
    from scipy.optimize import lsq_linear
    nu, target, sigma = map(np.asarray, (result.x, result.observed, result.sigma_values))
    columns = []
    for ref in methane:
        x = np.array([row["wavelength"] for row in ref.spectrum.rows])
        y = np.array([row["signal"] for row in ref.spectrum.rows])
        k = y * np.log(10) if "Absorbance" in ref.spectrum.signal_type else -np.log(y)
        order = np.argsort(x)
        columns.append(np.interp(nu, x[order], k[order]))
    u = 2 * (nu - nu[0]) / (nu[-1] - nu[0]) - 1
    design = np.column_stack(columns + [np.ones_like(u), u]) / sigma[:, None]
    for i, component in enumerate(result.components):
        remaining = np.delete(design, i, axis=1)
        lower = np.r_[np.zeros(len(methane) - 1), -np.inf, -np.inf]
        solution = lsq_linear(remaining, target / sigma, bounds=(lower, np.inf), method="bvls")
        q = np.sum((remaining @ solution.x - target / sigma) ** 2)
        assert component.delta_chi2 == pytest.approx(max(q - result.chi2, 0), rel=1e-8, abs=1e-5)


def test_source_metadata_conflicts_and_historical_threshold_equality(refs):
    reference = next(r for r in refs if r.molecule == "C2H2" and r.modality == "IR")
    blocked = identify(reference.spectrum, [reference], observation_metadata={"modality": "UV-Vis"})
    assert "metadata conflict" in blocked.components[0].reason
    first = identify(reference.spectrum, [reference])
    repeated = identify(reference.spectrum, [reference], threshold=first.components[0].sigma)
    assert repeated.components[0].reason == "Above conditional fit threshold"
    assert any("self-comparison" in warning for warning in repeated.warnings)


def test_disjoint_real_reference_subsets_block_before_empty_error_statistics(refs):
    reference = next(r for r in refs if r.molecule == "C2H2" and r.modality == "IR")
    # Only remove rows from a real measurement; no invented spectral values.
    rows = reference.spectrum.rows
    split = len(rows) // 2
    a = replace(reference, dataset_id="real-source-first-half",
                spectrum=replace(reference.spectrum, rows=rows[:split]))
    b = replace(reference, dataset_id="real-source-second-half",
                spectrum=replace(reference.spectrum, rows=rows[split:]))
    precision = float(np.min(np.diff(np.unique([row["signal"] for row in rows])))) / 2
    obs = replace(reference.spectrum, columns=reference.spectrum.columns + ("uncertainty",),
                  rows=tuple(dict(row, uncertainty=precision) for row in rows))
    result = identify(obs, [a, b])
    assert all(c.status == "blocked" and "common coverage" in c.reason for c in result.components)
