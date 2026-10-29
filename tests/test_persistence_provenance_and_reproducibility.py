"""Formal scientific test suite for persistence, provenance tracking, and exact calculation reproducibility.

Enforces Priority 6 requirements from the architecture review (Section 10):
1. Atomic writing and SHA-256 integrity verification.
2. Complete provenance retention across observation, metadata, and atmospheric forward model.
3. Distinction between stored-array reproduction and full raw-source regeneration.
4. Tamper detection and rejection of modified comparison records.
"""

from dataclasses import replace
import gc
import json
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication

from ecas.comparison.inputs import ComparisonInput
from ecas.comparison.persistence import (
    SCHEMA,
    build_comparison_record,
    load_comparison_record,
    reproduce_comparison_record,
)
from ecas.projects import ProjectStore
from ecas.ui.main_window import ECASWindow

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def window(tmp_path, qapp):
    widget = ECASWindow(
        projects_dir=tmp_path / "projects",
        reference_cache_dir=ROOT / "data/ExoMol/cache",
    )
    yield widget
    widget.close()
    gc.collect()


def test_saved_record_integrity_and_tamper_detection(tmp_path):
    """Verify that any modification to coordinates, values, or metadata invalidates integrity signature."""
    store = ProjectStore(tmp_path / "projects")
    store.create("tamper-proj")

    obs = ComparisonInput(
        source_id="real-obs",
        source_sha256="1" * 64,
        role="observation",
        observable="transit_depth",
        axis_unit="microns",
        signal_unit="percent",
        coordinate_frame="barycentric",
        response_id="passband-tophat",
        response_evidence="test response",
        coordinates=(2.0, 3.0, 4.0),
        values=(2.1, 2.2, 2.0),
    )
    model = replace(obs, source_id="real-model", role="forward_model", values=(2.0, 2.1, 2.0))

    record = build_comparison_record(
        left=obs,
        right=model,
        left_provenance={"kind": "real_observation", "source_file": "test.tbl"},
        right_provenance={
            "kind": "generated_isothermal_forward_model",
            "reference_type": "physical_reference_data",
            "contains_synthetic_templates": False,
            "physical_opacity_sources": ["POKAZATEL"],
        },
    )

    saved_file = store.save_comparison("tamper-proj", record)
    assert saved_file.is_file()

    # Valid load
    loaded = load_comparison_record(saved_file)
    assert loaded["schema"] == SCHEMA
    assert loaded["integrity_sha256"] is not None

    # Tampering with a residual or value must trigger integrity failure
    raw_text = saved_file.read_text(encoding="utf-8")
    tampered_text = raw_text.replace("2.1", "2.10001", 1)
    tampered_file = tmp_path / "tampered.json"
    tampered_file.write_text(tampered_text, encoding="utf-8")

    with pytest.raises(ValueError, match="integrity verification"):
        load_comparison_record(tampered_file)


def test_saved_record_distinguishes_raw_source_regeneration_vs_stored_reproduction(window, tmp_path):
    """Verify reopened saved comparison communicates source availability and regeneration feasibility."""
    window.project_browser.name.setText("priority6-provenance-study")
    window.project_browser.create_button.click()

    tbl_path = ROOT / "data/NASA/cache/entry-d39db942be204812b8d322bb17f554d8/source.tbl"
    window._import_csv_from_path(str(tbl_path))

    browser = window.comparison_browser
    browser.add_current_observation()
    browser.auto_fill_observation_metadata()

    # Generate model
    browser.generate_and_compare_forward_model()

    # Select candidate 0 (the full forward model with H2O POKAZATEL)
    browser.candidate_selector.setCurrentIndex(0)
    saved_record_path = browser.save_active_comparison()
    assert saved_record_path is not None and saved_record_path.is_file()

    # Clear staged session items and re-open saved record
    browser.clear_candidates_button.click()
    assert browser.diagnostic_panel.isHidden()

    browser.refresh_saved_comparisons()
    repro_check = browser.reproduce_selected_comparison()
    assert repro_check is not None
    assert repro_check.matches_saved_verdict is True
    assert repro_check.matches_saved_diagnostics is True

    # Check persistence status communicates raw source availability
    status_text = browser.persistence_status.text()
    assert "verdict matched, diagnostics matched" in status_text
    assert "raw source files were not re-ingested" in status_text
    assert "available on disk" in status_text
    assert "source.tbl" in status_text
    assert "full analysis can be regenerated from source" in status_text

    # Check compatibility text communicates integrity verification and physical references
    compat_text = browser.compatibility.text()
    assert "Integrity SHA-256 verified" in compat_text
    assert "Source file: source.tbl (available)" in compat_text
    assert "Opacities: POKAZATEL" in compat_text


def test_reopen_offline_record_where_source_file_is_unavailable(window, tmp_path):
    """Verify that an offline comparison record whose raw source file is missing still reproduces with clear notes."""
    store = ProjectStore(tmp_path / "projects")
    store.create("offline-proj")

    obs = ComparisonInput(
        source_id="offline-obs",
        source_sha256="3" * 64,
        role="observation",
        observable="transit_depth",
        axis_unit="microns",
        signal_unit="percent",
        coordinate_frame="barycentric",
        response_id="offline-passband",
        response_evidence="offline passband",
        coordinates=(2.0, 3.0, 4.0),
        values=(2.1, 2.2, 2.0),
    )
    model = replace(obs, source_id="offline-model", role="forward_model", values=(2.0, 2.0, 2.0))

    record = build_comparison_record(
        left=obs,
        right=model,
        left_provenance={
            "kind": "offline_observation",
            "source_file": "c:/missing/nonexistent/telescope_data.fits",
        },
        right_provenance={
            "kind": "generated_isothermal_forward_model",
            "reference_type": "physical_reference_data",
            "contains_synthetic_templates": False,
            "physical_opacity_sources": ["POKAZATEL"],
        },
    )
    saved_path = store.save_comparison("offline-proj", record)

    # Load in comparison browser
    browser = window.comparison_browser
    browser.saved_comparisons_selector.clear()
    browser.saved_comparisons_selector.addItem(saved_path.name, saved_path)
    browser.saved_comparisons_selector.setCurrentIndex(0)

    check = browser.reproduce_selected_comparison()
    assert check is not None
    assert check.matches_saved_verdict is True

    status_text = browser.persistence_status.text()
    assert "not found at its original path" in status_text
    assert "analysis reproduced from signed record snapshot" in status_text
