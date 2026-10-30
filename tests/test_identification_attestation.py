"""Tests for laboratory observation metadata attestation, conflict detection, and UI integration."""
from copy import deepcopy
from pathlib import Path
import numpy as np
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from ecas.identification.attestation import (
    audit_observation_attestation,
    attest_observation_context,
)
from ecas.identification.engine import identify
from ecas.identification.library import discover_library, load_reference
from ecas.identification_records import load_record, reproduce_record, save_record
from ecas.models.spectrum import SpectrumData
from ecas.observations import observation_context
from ecas.ui.identification_panel import IdentificationPanel
from ecas.ui.observation_attestation_dialog import ObservationAttestationDialog

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "data/ECAS_Spectral_Library/Ready_For_ECAS"
IR_REF = LIBRARY / "IR/CO2/CO2_gas_IR_index0.jdx"


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def generic_lab_spectrum(tmp_path: Path) -> SpectrumData:
    """Create a generic 2-column laboratory spectrum without embedded metadata."""
    file_path = tmp_path / "generic_ftir_sample.csv"
    # 100 wavenumber points from 2000 to 2500 cm^-1
    nu = np.linspace(2000.0, 2500.0, 100)
    # Simulated transmittance peak
    t = 95.0 - 40.0 * np.exp(-((nu - 2350.0) ** 2) / 100.0)
    rows = tuple({"wavelength": float(x), "signal": float(y)} for x, y in zip(nu, t))

    return SpectrumData(
        source_file=file_path,
        rows=rows,
        columns=("wavelength", "signal"),
        axis_unit=None,  # missing
        signal_unit=None,  # missing
        signal_type=None,  # missing
        warnings=(),
        metadata=(),  # no modality
    )


def test_audit_identifies_missing_generic_metadata(generic_lab_spectrum: SpectrumData):
    """Verify that an unattested generic spectrum is flagged as incomplete."""
    ctx = observation_context(generic_lab_spectrum, label="Generic Lab Sample")
    audit = audit_observation_attestation(ctx)

    assert audit.is_complete is False
    assert audit.can_identify is False
    assert "modality (IR or UV-Vis)" in audit.missing_fields
    assert "spectral coordinate unit (cm^-1, microns, or nm)" in audit.missing_fields
    assert "signal observable (absorbance, transmittance, optical_depth, or cross_section)" in audit.missing_fields
    assert "Incomplete: missing" in audit.summary_message


def test_attest_generic_spectrum_success(generic_lab_spectrum: SpectrumData):
    """Test successful explicit attestation of missing facts for a generic lab spectrum."""
    ctx = observation_context(generic_lab_spectrum, label="Generic Lab Sample")

    attested = attest_observation_context(
        ctx,
        modality="IR",
        axis_unit="cm^-1",
        signal_type="transmittance",
        signal_unit="%",
        notes="Per PerkinElmer Spectrum Two FTIR manual, %T vs cm^-1",
    )

    # Verify updated SpectrumData
    assert attested.spectrum.axis_unit == "cm^-1"
    assert attested.spectrum.signal_type == "transmittance"
    assert attested.spectrum.signal_unit == "%"

    # Verify metadata and provenance
    assert attested.metadata.get("modality") == "IR"
    prov = attested.metadata.get("metadata_provenance")
    assert prov is not None
    assert prov["user_attested"]["modality"] == "IR"
    assert prov["user_attested"]["axis_unit"] == "cm^-1"
    assert prov["user_attested"]["signal_type"] == "transmittance"
    assert prov["user_attested"]["signal_unit"] == "%"
    assert "PerkinElmer" in prov["attestation_notes"]

    # Re-audit should now be complete
    audit = audit_observation_attestation(attested)
    assert audit.is_complete is True
    assert audit.can_identify is True
    assert "IR transmittance [%] vs cm^-1" in audit.summary_message


def test_attestation_blocks_conflict_with_source_metadata():
    """Verify that user attestation cannot overwrite or contradict source facts."""
    ref = load_reference(IR_REF)
    ctx = observation_context(ref.spectrum, source_sha256=ref.source_sha256, label="CO2 Gas IR")

    # Source has modality='IR', axis_unit='1/CM', signal_type='Laboratory Absorbance', signal_unit='AU'
    # 1. Contradicting modality
    with pytest.raises(ValueError, match="conflicts with imported metadata"):
        attest_observation_context(ctx, modality="UV-Vis")

    # 2. Contradicting signal type
    with pytest.raises(ValueError, match="conflicts with imported metadata"):
        attest_observation_context(ctx, signal_type="transmittance")

    # 3. Contradicting signal unit
    with pytest.raises(ValueError, match="conflicts with imported metadata"):
        attest_observation_context(ctx, signal_unit="%")


def test_attestation_enforces_physical_consistency(generic_lab_spectrum: SpectrumData):
    """Verify that physically incompatible combinations are rejected."""
    ctx = observation_context(generic_lab_spectrum, label="Generic Lab Sample")

    # 1. Absorbance cannot have percent units
    with pytest.raises(ValueError, match="invalid for signal type 'absorbance'"):
        attest_observation_context(
            ctx,
            modality="IR",
            axis_unit="cm^-1",
            signal_type="absorbance",
            signal_unit="%",
        )

    # 2. Transmittance cannot have cm^2/molecule
    with pytest.raises(ValueError, match="invalid for signal type 'transmittance'"):
        attest_observation_context(
            ctx,
            modality="IR",
            axis_unit="cm^-1",
            signal_type="transmittance",
            signal_unit="cm^2/molecule",
        )

    # 3. IR modality cannot be cross section in laboratory fitting
    with pytest.raises(ValueError, match="IR laboratory identification requires absorbance or transmittance"):
        attest_observation_context(
            ctx,
            modality="IR",
            axis_unit="cm^-1",
            signal_type="cross_section",
            signal_unit="cm^2/molecule",
        )


def test_no_silent_inference_from_numbers_or_tabs(generic_lab_spectrum: SpectrumData):
    """Verify that numbers alone never infer modality without explicit user attestation."""
    ctx = observation_context(generic_lab_spectrum, label="Generic Lab Sample")

    # Even though numbers are in 2000-2500, modality is NOT assumed to be IR
    audit = audit_observation_attestation(ctx)
    assert audit.effective_facts["modality"] is None
    assert audit.is_complete is False


def test_attestation_dialog_interaction(app, generic_lab_spectrum: SpectrumData):
    """Test ObservationAttestationDialog population, input handling, and accept lifecycle."""
    ctx = observation_context(generic_lab_spectrum, label="Generic Lab Sample")

    dialog = ObservationAttestationDialog(ctx)
    dialog.show()

    # Verify source facts are displayed
    assert dialog.lbl_src_modality.text() == "(unspecified in file)"
    assert dialog.lbl_src_axis.text() == "(unspecified in file)"

    # Select values
    dialog.cmb_modality.setCurrentIndex(dialog.cmb_modality.findData("IR"))
    dialog.cmb_axis.setCurrentIndex(dialog.cmb_axis.findData("cm^-1"))
    dialog.cmb_signal_type.setCurrentIndex(dialog.cmb_signal_type.findData("transmittance"))
    dialog.cmb_signal_unit.setCurrentIndex(dialog.cmb_signal_unit.findData("%"))
    dialog.txt_notes.setText("Lab verified")

    dialog.btn_apply.click()

    assert dialog.attested_context is not None
    assert dialog.attested_context.metadata["modality"] == "IR"
    assert dialog.attested_context.spectrum.axis_unit == "cm^-1"
    dialog.close()


def test_identification_panel_attestation_and_fitting(app, generic_lab_spectrum: SpectrumData):
    """Verify end-to-end attestation in IdentificationPanel allows successful fitting."""
    ctx = observation_context(generic_lab_spectrum, label="Generic FTIR")
    ref = load_reference(IR_REF)

    panel = IdentificationPanel(lambda: (generic_lab_spectrum, None))
    panel._add_context(ctx)

    # Before attestation: preview shows missing attestation alert
    assert "Attestation required" in panel.plot_status.text()
    assert panel.attest_button.isEnabled() is True

    # Directly apply attestation
    attested = attest_observation_context(
        ctx,
        modality="IR",
        axis_unit="cm^-1",
        signal_type="transmittance",
        signal_unit="%",
        notes="Bench test",
    )
    panel.contexts[0] = attested
    panel._preview_observation(attested)

    assert "Attestation required" not in panel.plot_status.text()
    assert "[IR transmittance]" in panel.plot_status.text()

    # Select CO2 IR reference
    panel.molecule_checks[("IR", "CO2")].setChecked(True)
    panel.run_identification(synchronous=True)

    assert len(panel.batch_results) == 1
    context_out, result = panel.batch_results[0]
    assert context_out.metadata["modality"] == "IR"
    assert len(result.components) == 1
    assert result.components[0].molecule == "CO2"
    assert result.components[0].status == "evaluated"

    # Batch export and reproduction
    record = panel.analysis_record()
    reproduced = reproduce_record(record)
    assert len(reproduced) == 1
    assert reproduced[0].model == pytest.approx(result.model)

    panel.shutdown()
    panel.close()
