"""Comprehensive tests for ECAS Chunk 7: Scientific Resources, Interoperability, and Modeling."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import struct

import numpy as np
import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from ecas.comparison.alignment import (
    convert_signal_unit,
    convert_wavenumber_to_microns,
    restrict_to_shared_coordinates,
)
from ecas.comparison.candidates import evaluate_candidates
from ecas.comparison.eligibility import ComparisonInput, assess
from ecas.comparison.forward_model import OpacitySourceSpec
from ecas.comparison.inputs import observation_input
from ecas.comparison.model_adapters import (
    EXTERNAL_MODELING_SOFTWARE,
    export_external_forward_model,
    get_modeling_software_spec,
)
from ecas.comparison.persistence import (
    build_comparison_record,
    load_comparison_record,
    reproduce_comparison_record,
)
from ecas.ingestion.csv_importer import SpectrumImportError
from ecas.ingestion.nasa_table import import_transmission_table
from ecas.ingestion.tabular_formats import (
    import_ascii_spectrum,
    import_ecsv_spectrum,
    import_fits_bintable_spectrum,
    import_tabular_spectrum,
)
from ecas.resources.catalog import (
    BENCHMARK_PLANETS,
    CATEGORY_FILTERS,
    EVIDENCE_STATUSES,
    MOLECULAR_DATABASE_SPECS,
    SCIENTIFIC_RESOURCES,
    filter_resources,
    get_benchmark_planet,
    get_molecular_database_spec,
    get_resource_by_id,
    validate_temperature_applicability,
)
from ecas.ui.main_window import ECASWindow
from ecas.ui.resources_browser import ResourcesBrowser


def _fits_card(keyword: str, value_str: str, comment: str = "") -> bytes:
    if keyword == "END":
        line = "END"
    else:
        line = f"{keyword:<8}= {value_str:>20}"
        if comment:
            line += f" / {comment}"
    return line[:80].ljust(80, " ").encode("ascii")


def _pad_fits_block(raw: bytes) -> bytes:
    rem = len(raw) % 2880
    return raw if rem == 0 else raw + (b" " * (2880 - rem))


def _build_test_fits_bintable(rows: list[tuple[float, float, float]]) -> bytes:
    primary_cards = [
        _fits_card("SIMPLE", "T", "Standard FITS"),
        _fits_card("BITPIX", "8", "8-bit bytes"),
        _fits_card("NAXIS", "0", "No primary array"),
        _fits_card("EXTEND", "T", "Extensions present"),
        _fits_card("OBJECT", "'WASP-39 b'"),
        _fits_card("SPEC_TYP", "'Transmission'"),
        _fits_card("END", ""),
    ]
    primary_block = _pad_fits_block(b"".join(primary_cards))

    ext_cards = [
        _fits_card("XTENSION", "'BINTABLE'", "Binary table extension"),
        _fits_card("BITPIX", "8"),
        _fits_card("NAXIS", "2"),
        _fits_card("NAXIS1", "24", "3 float64 columns = 24 bytes"),
        _fits_card("NAXIS2", str(len(rows))),
        _fits_card("PCOUNT", "0"),
        _fits_card("GCOUNT", "1"),
        _fits_card("TFIELDS", "3"),
        _fits_card("TTYPE1", "'wavelength'"),
        _fits_card("TFORM1", "'1D'"),
        _fits_card("TUNIT1", "'um'"),
        _fits_card("TTYPE2", "'transit_depth'"),
        _fits_card("TFORM2", "'1D'"),
        _fits_card("TUNIT2", "'ppm'"),
        _fits_card("TTYPE3", "'uncertainty'"),
        _fits_card("TFORM3", "'1D'"),
        _fits_card("TUNIT3", "'ppm'"),
        _fits_card("END", ""),
    ]
    ext_header_block = _pad_fits_block(b"".join(ext_cards))
    data_bytes = b"".join(struct.pack(">ddd", w, d, u) for w, d, u in rows)
    rem = len(data_bytes) % 2880
    if rem != 0:
        data_bytes += b"\x00" * (2880 - rem)
    return primary_block + ext_header_block + data_bytes


def test_scientific_resource_catalog_integrity_and_filtering():
    assert len(SCIENTIFIC_RESOURCES) >= 17
    seen_ids = set()
    categories_present = set()
    for res in SCIENTIFIC_RESOURCES:
        assert res.resource_id not in seen_ids
        seen_ids.add(res.resource_id)
        categories_present.add(res.category)
        assert res.canonical_url.startswith("https://")
        assert "?" not in res.canonical_url and "#" not in res.canonical_url
        assert get_resource_by_id(res.resource_id) == res

    assert categories_present == set(CATEGORY_FILTERS) - {"All"}

    software = filter_resources(category="Software")
    software_titles = {r.title for r in software}
    assert {"petitRADTRANS", "POSEIDON", "TauREx 3", "PLATON", "Pyrat Bay"} <= software_titles

    archives = filter_resources(category="Data archive")
    archive_titles = {r.title for r in archives}
    assert {"NASA Exoplanet Archive", "Mikulski Archive for Space Telescopes (MAST)"} <= archive_titles

    wasp39_matches = filter_resources(query="10.1038/s41586-022-05674-1")
    assert len(wasp39_matches) == 1
    assert "WASP-39" in wasp39_matches[0].title


def test_molecular_database_temperature_applicability_and_benchmarks():
    assert len(MOLECULAR_DATABASE_SPECS) == 5
    exomol = get_molecular_database_spec("ExoMol")
    hitran = get_molecular_database_spec("HITRAN")
    assert exomol is not None and hitran is not None

    # Hot-Jupiter temperature (1200 K): HITRAN & GEISA warn; ExoMol & HITEMP are applicable
    is_ok_hitran, hitran_warn = validate_temperature_applicability("HITRAN", 1200.0)
    assert is_ok_hitran is False and "exceeds HITRAN typical upper applicability" in hitran_warn
    assert validate_temperature_applicability("ExoMol", 1200.0)[0] is True
    assert validate_temperature_applicability("HITEMP", 1200.0)[0] is True
    assert validate_temperature_applicability("HITRAN", 296.0)[0] is True

    # Benchmark planet evidence statuses
    wasp39 = get_benchmark_planet("WASP-39 b")
    k2_18 = get_benchmark_planet("K2-18 b")
    assert wasp39 is not None and k2_18 is not None
    wasp39_by_species = {rec.species: rec for rec in wasp39.species_assessments}
    assert wasp39_by_species["CO2"].status == "independent_confirmation"
    assert wasp39_by_species["SO2"].status == "independent_confirmation"
    assert wasp39_by_species["CH4"].status == "upper_limit_or_non_detection"

    k2_by_species = {rec.species: rec for rec in k2_18.species_assessments}
    assert k2_by_species["CH4"].status == "reported_detection"
    assert k2_by_species["DMS"].status == "tentative_or_disputed"
    for planet in BENCHMARK_PLANETS:
        for assessment in planet.species_assessments:
            assert assessment.status in EVIDENCE_STATUSES


def test_resources_browser_ui_filters_and_copies_to_clipboard():
    app = QApplication.instance() or QApplication([])
    browser = ResourcesBrowser()

    assert browser.active_category == "All"
    assert browser.resource_table.rowCount() == len(SCIENTIFIC_RESOURCES)

    # Filter by category button click
    browser.category_buttons["Software"].click()
    assert browser.active_category == "Software"
    assert browser.resource_table.rowCount() == 5

    # Filter by search input
    browser.search_input.setText("petitRADTRANS")
    assert browser.resource_table.rowCount() == 1
    selected = browser.selected_resource()
    assert selected is not None and selected.title == "petitRADTRANS"

    # Copy canonical link and citation
    copied_url = browser.copy_selected_link()
    assert copied_url == "https://petitradtrans.readthedocs.io/en/latest/"
    assert QGuiApplication.clipboard().text() == copied_url
    assert "Copied canonical link" in browser.copy_status.text()

    copied_citation = browser.copy_selected_citation()
    assert "Molli" in copied_citation
    assert "10.1051/0004-6361/201935470" in copied_citation
    assert QGuiApplication.clipboard().text() == copied_citation

    browser.close()


def test_ecsv_ascii_and_fits_importers_and_lab_ftir_separation(tmp_path):
    # 1. Astropy ECSV planetary transmission spectrum
    ecsv_file = tmp_path / "wasp39b_ers.ecsv"
    ecsv_file.write_text(
        "# %ECSV 1.0\n"
        "# ---\n"
        "# delimiter: ','\n"
        "# meta:\n"
        "#   signal_type: Transmission\n"
        "#   pl_name: WASP-39 b\n"
        "# datatype:\n"
        "# - {name: wavelength, unit: um, datatype: float64}\n"
        "# - {name: transit_depth, unit: ppm, datatype: float64}\n"
        "# - {name: uncertainty, unit: ppm, datatype: float64}\n"
        "wavelength,transit_depth,uncertainty\n"
        "3.80,21400.0,150.0\n"
        "4.30,22350.0,140.0\n"
        "4.80,21500.0,160.0\n",
        encoding="utf-8",
    )
    ecsv_spec = import_ecsv_spectrum(ecsv_file)
    assert ecsv_spec.row_count == 3
    assert ecsv_spec.axis_unit == "um"
    assert ecsv_spec.signal_unit == "ppm"
    assert ecsv_spec.signal_type == "Transmission"
    assert ecsv_spec.rows[1]["wavelength"] == 4.30
    assert ecsv_spec.rows[1]["signal"] == 22350.0
    assert ecsv_spec.rows[1]["uncertainty"] == 140.0

    # 2. Laboratory FTIR spectrum (.dat) with wavenumber and absorbance
    lab_file = tmp_path / "co2_lab_ftir.dat"
    lab_file.write_text(
        "# Laboratory FTIR cell measurement (T = 296 K, P = 1 atm)\n"
        "# wavenumber absorbance uncertainty\n"
        "2250.0 0.12 0.01\n"
        "2349.0 1.45 0.02\n"
        "2400.0 0.08 0.01\n",
        encoding="utf-8",
    )
    lab_spec = import_ascii_spectrum(lab_file)
    assert lab_spec.axis_unit == "cm^-1"
    assert lab_spec.signal_unit == "absorbance"
    assert lab_spec.signal_type == "Laboratory FTIR Absorbance"
    assert any("laboratory spectra are not planetary transit-depth observations" in w for w in lab_spec.warnings)

    # Verify observation_input does NOT promote laboratory FTIR absorbance to transit_depth
    adapted_lab = observation_input(lab_spec, source_sha256="a" * 64)
    assert adapted_lab.comparison_input.observable is None

    # 3. FITS BINTABLE spectrum (.fits)
    fits_file = tmp_path / "jwst_nirspec.fits"
    fits_bytes = _build_test_fits_bintable(
        [(2.5, 21100.0, 120.0), (3.5, 21300.0, 110.0), (4.3, 22400.0, 130.0)]
    )
    fits_file.write_bytes(fits_bytes)
    fits_spec = import_fits_bintable_spectrum(fits_file)
    assert fits_spec.row_count == 3
    assert fits_spec.axis_unit == "um"
    assert fits_spec.signal_unit == "ppm"
    assert fits_spec.signal_type == "Transmission"
    assert fits_spec.rows[2]["wavelength"] == pytest.approx(4.3)
    assert fits_spec.rows[2]["signal"] == pytest.approx(22400.0)

    # Verify ECASWindow can load .ecsv and .fits directly
    app = QApplication.instance() or QApplication([])
    window = ECASWindow(projects_dir=tmp_path / "projects", reference_cache_dir=tmp_path / "cache")
    window._import_csv_from_path(str(fits_file))
    assert window.current_spectrum is not None
    assert window.current_spectrum.row_count == 3
    assert window.current_source_sha256 == sha256(fits_bytes).hexdigest()
    window.close()


def test_wavenumber_to_microns_reverses_axis_and_permutes_covariance():
    # Strictly increasing wavenumbers: 2000, 2500, 4000, 5000 cm^-1 -> 5.0, 4.0, 2.5, 2.0 microns
    nu = (2000.0, 2500.0, 4000.0, 5000.0)
    vals = (0.021, 0.024, 0.022, 0.020)
    sigma = (0.001, 0.002, 0.0015, 0.0012)
    base_cov = np.array(
        [
            [1.0e-6, 0.2e-6, 0.0, 0.0],
            [0.2e-6, 4.0e-6, 0.3e-6, 0.0],
            [0.0, 0.3e-6, 2.25e-6, 0.1e-6],
            [0.0, 0.0, 0.1e-6, 1.44e-6],
        ],
        dtype=float,
    )
    item = ComparisonInput(
        source_id="wavenumber-obs",
        source_sha256="b" * 64,
        role="observation",
        observable="transit_depth",
        axis_unit="cm^-1",
        signal_unit="fraction",
        coordinate_frame="barycentric",
        response_id="inst-1",
        response_evidence="Calibrated",
        coordinates=nu,
        values=vals,
        noise_kind="full_covariance",
        noise_evidence="Pipeline covariance",
        sigma=sigma,
        covariance=tuple(tuple(float(v) for v in row) for row in base_cov),
    )

    transformed = convert_wavenumber_to_microns(item)
    out = transformed.transformed
    assert out.axis_unit == "microns"
    assert out.coordinates == pytest.approx((2.0, 2.5, 4.0, 5.0))
    assert out.values == pytest.approx((0.020, 0.022, 0.024, 0.021))
    assert out.sigma == pytest.approx((0.0012, 0.0015, 0.002, 0.001))
    assert transformed.steps[0].operation == "convert_wavenumber_to_microns_v1"
    assert transformed.steps[0].included_indices == (3, 2, 1, 0)

    # Verify quadratic form invariance r^T C^-1 r under permutation
    r_orig = np.array([0.0005, -0.0011, 0.0008, -0.0003])
    r_perm = r_orig[[3, 2, 1, 0]]
    cov_perm = np.asarray(out.covariance, dtype=float)
    chi2_orig = float(r_orig @ np.linalg.solve(base_cov, r_orig))
    chi2_perm = float(r_perm @ np.linalg.solve(cov_perm, r_perm))
    assert chi2_perm == pytest.approx(chi2_orig, rel=1e-12, abs=1e-12)


def test_external_forward_model_adapters_and_wasp39b_benchmark_workflow(tmp_path):
    assert len(EXTERNAL_MODELING_SOFTWARE) == 5
    for code_id in ("petitradtrans", "poseidon", "taurex3", "platon", "pyratbay"):
        spec = get_modeling_software_spec(code_id)
        assert spec.catalog_resource.canonical_url.startswith("https://")

    # Load real bundled NASA WASP-39 b NIRISS SOSS table (feinstein-2023.tbl)
    nasa_tbl_path = (
        Path(__file__).resolve().parents[1] / "data" / "NASA" / "2026-10-27" / "feinstein-2023.tbl"
    )
    details = import_transmission_table(nasa_tbl_path)
    obs_coords = tuple(float(r["wavelength"]) for r in details.spectrum.rows[:12])
    obs_vals = tuple(float(r["signal"]) for r in details.spectrum.rows[:12])
    obs_sig = tuple(
        max(abs(float(r["pl_trandeperr1"])), abs(float(r["pl_trandeperr2"])))
        for r in details.spectrum.rows[:12]
    )

    obs_input = ComparisonInput(
        source_id=str(nasa_tbl_path),
        source_sha256=details.source_sha256,
        role="observation",
        observable="transit_depth",
        axis_unit="microns",
        signal_unit="percent",
        coordinate_frame="barycentric",
        response_id="JWST-NIRISS-SOSS-feinstein2023",
        response_evidence="Feinstein et al. (2023) instrument profile",
        coordinates=obs_coords,
        values=obs_vals,
        noise_kind="diagonal_1sigma",
        noise_evidence="Published asymmetric bounds conservatively enveloped",
        sigma=obs_sig,
    )

    # Export a petitRADTRANS forward model (close to observation) using ExoMol + HITEMP at 1150 K
    prt_path = tmp_path / "wasp39b_prt_solar_10x.json"
    prt_adapted = export_external_forward_model(
        output_path=prt_path,
        software_id="petitradtrans",
        engine_version="3.0.0",
        coordinates=obs_coords,
        values=tuple(v + 0.004 for v in obs_vals),
        input_axis_unit="microns",
        input_signal_unit="percent",
        representative_temperature_k=1150.0,
        temperature_pressure_profile="Guillot (2010) T_eq=1150 K",
        abundance_convention="10x solar equilibrium chemistry + photochemistry",
        species_parameters=(("H2O", 1e-3), ("CO2", 5e-5), ("SO2", 5e-6)),
        opacity_sources=(
            OpacitySourceSpec("H2O", "1H2-16O", "ExoMol POKAZATEL", "2018", "1" * 64),
            OpacitySourceSpec("CO2", "12C-16O2", "HITEMP 2020", "2020", "2" * 64),
        ),
        gravity_m_s2=4.26,
        reference_pressure_bar=0.01,
        planet_radius_m=9.14e7,
        stellar_radius_m=6.26e8,
        continuum_and_clouds="H2-He CIA + gray cloud deck at 10 mbar",
        coordinate_frame="barycentric",
        response_id="JWST-NIRISS-SOSS-feinstein2023",
        response_evidence="Convolved to Feinstein et al. (2023) NIRISS SOSS kernel",
    )
    assert prt_adapted.applicability_warnings == ()

    # Export a PLATON forward model in SI meters and fraction units, using HITRAN at 1150 K (triggers warning!)
    platon_path = tmp_path / "wasp39b_platon_1x.json"
    platon_adapted = export_external_forward_model(
        output_path=platon_path,
        software_id="platon",
        engine_version="6.2",
        coordinates=tuple(w * 1e-6 for w in obs_coords),
        values=tuple((v + 0.035) * 0.01 for v in obs_vals),
        input_axis_unit="m",
        input_signal_unit="fraction",
        representative_temperature_k=1150.0,
        temperature_pressure_profile="Isothermal 1150 K",
        abundance_convention="1x solar equilibrium",
        species_parameters=(("H2O", 1e-4), ("CO2", 1e-6)),
        opacity_sources=(
            OpacitySourceSpec("CO2", "12C-16O2", "HITRAN 2020", "2020", "3" * 64),
        ),
        gravity_m_s2=4.26,
        reference_pressure_bar=0.01,
        planet_radius_m=9.14e7,
        stellar_radius_m=6.26e8,
        continuum_and_clouds="Cloud-free H2-He CIA",
        coordinate_frame="barycentric",
        response_id="JWST-NIRISS-SOSS-feinstein2023",
        response_evidence="Convolved to Feinstein et al. (2023) NIRISS SOSS kernel",
    )
    assert len(platon_adapted.applicability_warnings) == 1
    assert "HITRAN" in platon_adapted.applicability_warnings[0]

    # Convert PLATON model from fraction to percent explicitly via convert_signal_unit
    platon_percent = convert_signal_unit(platon_adapted.loaded_model.comparison_input, "percent")

    # Evaluate candidates against the WASP-39 b observation
    summary = evaluate_candidates(
        obs_input,
        (prt_adapted.loaded_model.comparison_input, platon_percent.transformed),
    )
    assert summary.eligible_indices == (0, 1)
    assert summary.ordered_eligible_indices == (0, 1)

    # Persist and reproduce the comparison record
    record = build_comparison_record(
        obs_input,
        platon_percent,
        left_provenance={"source": "NASA Exoplanet Archive feinstein-2023.tbl"},
        right_provenance=platon_adapted.loaded_model.to_provenance_dict(),
    )
    rec_path = tmp_path / "wasp39b_comparison_record.json"
    import json
    rec_path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    loaded_rec = load_comparison_record(rec_path)
    repro = reproduce_comparison_record(loaded_rec)
    assert repro.matches_saved_verdict is True
    assert repro.matches_saved_diagnostics is True
    assert repro.discrepancies == ()


def test_taurex3_wavenumber_adapter_and_tabular_rejection_guards(tmp_path):
    # TauREx 3 model exported on an increasing wavenumber grid (2000, 2500, 4000 cm^-1 -> 5.0, 4.0, 2.5 um)
    taurex_path = tmp_path / "taurex_wavenumber_model.json"
    adapted = export_external_forward_model(
        output_path=taurex_path,
        software_id="taurex3",
        engine_version="3.1.2",
        coordinates=(2000.0, 2500.0, 4000.0),
        values=(21500.0, 22400.0, 21100.0),
        input_axis_unit="cm^-1",
        input_signal_unit="ppm",
        representative_temperature_k=1100.0,
        temperature_pressure_profile="Isothermal 1100 K",
        abundance_convention="Constant VMR",
        species_parameters=(("H2O", 1e-3), ("CO2", 1e-4)),
        opacity_sources=(
            OpacitySourceSpec("H2O", "1H2-16O", "ExoMol POKAZATEL", "2018", "a" * 64),
        ),
        gravity_m_s2=4.26,
        reference_pressure_bar=0.01,
        planet_radius_m=9.14e7,
        stellar_radius_m=6.26e8,
        continuum_and_clouds="Lee Mie clouds + Rayleigh",
    )
    comp = adapted.loaded_model.comparison_input
    assert comp.axis_unit == "microns"
    assert comp.signal_unit == "fraction"
    assert comp.coordinates == pytest.approx((2.5, 4.0, 5.0))
    assert comp.values == pytest.approx((0.0211, 0.0224, 0.0215))

    # Reject malformed ECSV without %ECSV header
    bad_ecsv = tmp_path / "bad.ecsv"
    bad_ecsv.write_text("wavelength,signal\n1.0,2.0\n", encoding="utf-8")
    with pytest.raises(SpectrumImportError, match="%ECSV"):
        import_ecsv_spectrum(bad_ecsv)

    # Reject FITS file whose byte length is not a multiple of 2880
    bad_fits = tmp_path / "bad.fits"
    bad_fits.write_bytes(b"SIMPLE  =                    T" + b" " * 100)
    with pytest.raises(SpectrumImportError, match="multiple of 2880"):
        import_fits_bintable_spectrum(bad_fits)

    # Reject ASCII file with negative uncertainty
    bad_dat = tmp_path / "neg_unc.dat"
    bad_dat.write_text("wavelength signal uncertainty\n1.0 0.02 -0.001\n", encoding="utf-8")
    with pytest.raises(SpectrumImportError, match="Negative uncertainty"):
        import_tabular_spectrum(bad_dat)

