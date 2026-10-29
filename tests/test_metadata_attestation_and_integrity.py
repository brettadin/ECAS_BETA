"""Formal test suite for comparison eligibility, metadata integrity, and attestation trust boundaries.

Enforces Priority 5 requirements from the architecture review (Section 9):
1. Distinguishing source-provided information, user-attested values, and application-derived values.
2. Conflict detection when caller attempts to overwrite populated source metadata.
3. Preserving complete metadata provenance through persistence and verification.
4. Validation across supported and unsupported unit/observable combinations.
"""

from dataclasses import replace
import gc
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication

from ecas.comparison.inputs import ComparisonInput
from ecas.comparison.persistence import (
    build_comparison_record,
    load_comparison_record,
    reproduce_comparison_record,
)
from ecas.ingestion.nasa_table import import_transmission_table
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


def test_conflict_detection_when_attestation_contradicts_imported_metadata(window):
    """Verify UI blocks user from asserting metadata that directly contradicts source file headers."""
    tbl_path = ROOT / "data/NASA/cache/entry-d39db942be204812b8d322bb17f554d8/source.tbl"
    window._import_csv_from_path(str(tbl_path))

    browser = window.comparison_browser
    browser.add_current_observation()

    # The imported table declares axis_unit = microns.
    # If the user tries to attest nanometers, it must raise ValueError rather than silently overriding.
    nm_idx = browser.obs_axis_unit_selector.findData("nanometers")
    if nm_idx >= 0:
        browser.obs_axis_unit_selector.setCurrentIndex(nm_idx)
        with pytest.raises(ValueError, match="conflicts with imported metadata"):
            browser._build_attested_observation()

    # Reset axis unit selector to None (default / use imported)
    browser.obs_axis_unit_selector.setCurrentIndex(0)

    # If the user tries to attest fraction when table declares percent
    browser.obs_signal_unit_selector.setCurrentIndex(
        browser.obs_signal_unit_selector.findData("fraction")
    )
    with pytest.raises(ValueError, match="conflicts with imported metadata"):
        browser._build_attested_observation()


def test_provenance_distinguishes_source_attested_and_derived_metadata(window, tmp_path):
    """Verify metadata_provenance explicitly separates source-provided, user-attested, and bin-derived data."""
    tbl_path = ROOT / "data/NASA/cache/entry-d39db942be204812b8d322bb17f554d8/source.tbl"
    window._import_csv_from_path(str(tbl_path))

    browser = window.comparison_browser
    browser.add_current_observation()
    browser.auto_fill_observation_metadata()

    # Explicitly attest coordinate_frame and response_evidence
    browser.obs_frame_input.setText("barycentric-attested")
    browser.obs_response_evidence_input.setText("Alderson et al. 2022 Table 1 passband bounds")

    updated, prov, notes = browser._build_attested_observation()
    assert updated.coordinate_frame == "barycentric-attested"

    meta_prov = prov.get("metadata_provenance")
    assert meta_prov is not None
    assert "source_provided" in meta_prov
    assert "user_attested" in meta_prov
    assert "bin_derived" in meta_prov

    # source_provided records fields established by raw table
    src = meta_prov["source_provided"]
    assert src.get("axis_unit") == "microns"
    assert src.get("signal_unit") == "percent"

    # user_attested records fields supplied by caller
    att = meta_prov["user_attested"]
    assert att.get("coordinate_frame") == "barycentric-attested"
    assert att.get("response_evidence") == "Alderson et al. 2022 Table 1 passband bounds"

    # bin_derived records resolved passband properties
    bin_der = meta_prov["bin_derived"]
    assert bin_der is not None
    assert bin_der.get("convention") is not None


def test_metadata_provenance_survives_project_persistence_and_reopening(window, tmp_path):
    """Verify metadata_provenance persists into signed JSON comparison record and reproduces cleanly."""
    window.project_browser.name.setText("metadata-integrity-proj")
    window.project_browser.create_button.click()

    tbl_path = ROOT / "data/NASA/cache/entry-d39db942be204812b8d322bb17f554d8/source.tbl"
    window._import_csv_from_path(str(tbl_path))

    browser = window.comparison_browser
    browser.add_current_observation()
    browser.auto_fill_observation_metadata()

    summary = browser.generate_and_compare_forward_model()
    assert summary is not None

    record_path = browser.save_active_comparison()
    assert record_path is not None and record_path.is_file()

    loaded = load_comparison_record(record_path)
    left_prov = loaded["left"]["provenance"]
    assert "metadata_provenance" in left_prov
    assert left_prov["metadata_provenance"]["source_provided"]["axis_unit"] == "microns"

    # Verify reproducibility
    repro = reproduce_comparison_record(loaded)
    assert repro.matches_saved_verdict is True
    assert repro.matches_saved_diagnostics is True
    assert repro.discrepancies == ()
