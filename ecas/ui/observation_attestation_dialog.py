"""Interactive dialog for explicit laboratory observation metadata attestation."""
from __future__ import annotations

from typing import cast
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ecas.identification.attestation import (
    audit_observation_attestation,
    attest_observation_context,
)
from ecas.observations import ObservationContext


class ObservationAttestationDialog(QDialog):
    """Dialog allowing users to explicitly attest missing laboratory metadata."""

    def __init__(self, context: ObservationContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Attest Observation Metadata — ECAS")
        self.resize(680, 560)

        self.context = context
        self.audit = audit_observation_attestation(context)
        self.attested_context: ObservationContext | None = None

        self._setup_ui()
        self._populate_fields()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # 1. Scientific banner
        banner = QFrame()
        banner.setFrameShape(QFrame.StyledPanel)
        banner.setStyleSheet(
            "background-color: #26292e; border: 1px solid #4f5b66; border-radius: 4px; padding: 6px;"
        )
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(8, 4, 8, 4)
        b_lbl = QLabel(
            "<b>Explicit Laboratory Metadata Attestation:</b> "
            "Source-provided file facts take precedence and cannot be overridden. "
            "Missing experimental conditions (modality, coordinate units, signal observable) "
            "must be attested explicitly with documentary evidence. "
            "ECAS never infers physical units from measurement values or active UI tabs."
        )
        b_lbl.setWordWrap(True)
        b_lbl.setStyleSheet("color: #cad3f5; font-size: 11px;")
        b_layout.addWidget(b_lbl)
        main_layout.addWidget(banner)

        # 2. Source Facts (Read-Only) Group
        src_group = QGroupBox("Imported Source Facts (Immutable)")
        src_form = QFormLayout(src_group)
        src_form.setSpacing(5)

        self.lbl_file = QLabel(str(self.context.spectrum.source_file.name))
        self.lbl_id = QLabel(self.context.observation_id)
        self.lbl_digest = QLabel(self.context.source_sha256 or "(none / snapshot)")
        self.lbl_src_modality = QLabel("-")
        self.lbl_src_axis = QLabel("-")
        self.lbl_src_signal = QLabel("-")

        for lbl in (self.lbl_file, self.lbl_id, self.lbl_digest, self.lbl_src_modality, self.lbl_src_axis, self.lbl_src_signal):
            lbl.setStyleSheet("color: #a6adc8; font-family: monospace;")
            lbl.setWordWrap(True)

        src_form.addRow("Source File:", self.lbl_file)
        src_form.addRow("Observation ID:", self.lbl_id)
        src_form.addRow("SHA-256 Digest:", self.lbl_digest)
        src_form.addRow("Source Modality:", self.lbl_src_modality)
        src_form.addRow("Source Axis Unit:", self.lbl_src_axis)
        src_form.addRow("Source Signal:", self.lbl_src_signal)
        main_layout.addWidget(src_group)

        # 3. User Attestation Group
        att_group = QGroupBox("User-Attested Experimental Conditions")
        att_form = QFormLayout(att_group)
        att_form.setSpacing(8)

        # Modality
        self.cmb_modality = QComboBox()
        self.cmb_modality.addItem("Select Modality...", None)
        self.cmb_modality.addItem("IR (Infrared Spectroscopy)", "IR")
        self.cmb_modality.addItem("UV-Vis (Ultraviolet-Visible Spectroscopy)", "UV-Vis")
        self.cmb_modality.currentIndexChanged.connect(self._on_modality_changed)
        att_form.addRow("Modality:", self.cmb_modality)

        # Coordinate unit
        self.cmb_axis = QComboBox()
        self.cmb_axis.addItem("Select Spectral Coordinate...", None)
        self.cmb_axis.addItem("Wavenumber: cm^-1", "cm^-1")
        self.cmb_axis.addItem("Wavelength: microns (μm)", "microns")
        self.cmb_axis.addItem("Wavelength: nanometers (nm)", "nm")
        att_form.addRow("Spectral Coordinate:", self.cmb_axis)

        # Signal Observable
        self.cmb_signal_type = QComboBox()
        self.cmb_signal_type.addItem("Select Signal Observable...", None)
        self.cmb_signal_type.addItem("Transmittance", "transmittance")
        self.cmb_signal_type.addItem("Absorbance", "absorbance")
        self.cmb_signal_type.addItem("Optical Depth", "optical_depth")
        self.cmb_signal_type.addItem("Absorption Cross Section", "cross_section")
        self.cmb_signal_type.currentIndexChanged.connect(self._on_signal_type_changed)
        att_form.addRow("Signal Observable:", self.cmb_signal_type)

        # Signal Unit
        self.cmb_signal_unit = QComboBox()
        self.cmb_signal_unit.addItem("Select Signal Unit...", None)
        att_form.addRow("Signal Unit:", self.cmb_signal_unit)

        # Attestation Notes / Documentation
        self.txt_notes = QLineEdit()
        self.txt_notes.setPlaceholderText("e.g. PerkinElmer Spectrum Two FTIR manual; transmittance % vs cm^-1")
        att_form.addRow("Evidence / Notes:", self.txt_notes)

        main_layout.addWidget(att_group)
        main_layout.addStretch(1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton("Apply Attestation")
        self.btn_apply.setDefault(True)
        self.btn_apply.setStyleSheet("font-weight: bold; padding: 5px 12px;")
        self.btn_apply.clicked.connect(self._on_apply)
        btn_layout.addWidget(self.btn_apply)

        main_layout.addLayout(btn_layout)

    def _populate_fields(self) -> None:
        src = self.audit.source_facts
        user = self.audit.user_attested

        # Populate source facts display
        self.lbl_src_modality.setText(src.get("modality") or "(unspecified in file)")
        self.lbl_src_axis.setText(src.get("axis_unit") or "(unspecified in file)")
        sig_str = f"{src.get('signal_type') or '(unspecified)'} [{src.get('signal_unit') or '(unspecified)'}]"
        self.lbl_src_signal.setText(sig_str)

        # 1. Modality
        if src.get("modality"):
            self.cmb_modality.clear()
            self.cmb_modality.addItem(f"{src['modality']} (Source-declared)", src["modality"])
            self.cmb_modality.setEnabled(False)
        elif user.get("modality"):
            idx = self.cmb_modality.findData(user["modality"])
            if idx >= 0:
                self.cmb_modality.setCurrentIndex(idx)

        # 2. Axis Unit
        if src.get("axis_unit"):
            self.cmb_axis.clear()
            self.cmb_axis.addItem(f"{src['axis_unit']} (Source-declared)", src["axis_unit"])
            self.cmb_axis.setEnabled(False)
        elif user.get("axis_unit"):
            idx = self.cmb_axis.findData(user["axis_unit"])
            if idx >= 0:
                self.cmb_axis.setCurrentIndex(idx)

        # 3. Signal Type
        if src.get("signal_type"):
            self.cmb_signal_type.clear()
            self.cmb_signal_type.addItem(f"{src['signal_type']} (Source-declared)", src["signal_type"])
            self.cmb_signal_type.setEnabled(False)
            self._update_signal_units(src["signal_type"])
        elif user.get("signal_type"):
            idx = self.cmb_signal_type.findData(user["signal_type"])
            if idx >= 0:
                self.cmb_signal_type.setCurrentIndex(idx)
                self._update_signal_units(user["signal_type"])

        # 4. Signal Unit
        if src.get("signal_unit"):
            self.cmb_signal_unit.clear()
            self.cmb_signal_unit.addItem(f"{src['signal_unit']} (Source-declared)", src["signal_unit"])
            self.cmb_signal_unit.setEnabled(False)
        elif user.get("signal_unit"):
            idx = self.cmb_signal_unit.findData(user["signal_unit"])
            if idx >= 0:
                self.cmb_signal_unit.setCurrentIndex(idx)

        # 5. Notes
        if user.get("notes"):
            self.txt_notes.setText(str(user["notes"]))

    def _on_modality_changed(self) -> None:
        mod = self.cmb_modality.currentData()
        if mod == "IR" and self.cmb_signal_type.currentData() == "cross_section":
            self.cmb_signal_type.setCurrentIndex(0)
        elif mod == "UV-Vis" and self.cmb_signal_type.currentData() in ("transmittance", "absorbance"):
            # Informative or default to cross section if empty
            pass

    def _on_signal_type_changed(self) -> None:
        st = self.cmb_signal_type.currentData()
        self._update_signal_units(st)

    def _update_signal_units(self, signal_type: str | None) -> None:
        if self.audit.source_facts.get("signal_unit"):
            return

        self.cmb_signal_unit.blockSignals(True)
        self.cmb_signal_unit.clear()
        self.cmb_signal_unit.addItem("Select Signal Unit...", None)

        if not signal_type:
            self.cmb_signal_unit.blockSignals(False)
            return

        st = signal_type.lower()
        if "transmittance" in st:
            self.cmb_signal_unit.addItem("Percent (%)", "%")
            self.cmb_signal_unit.addItem("Fraction (0 to 1)", "fraction")
            self.cmb_signal_unit.setCurrentIndex(1)  # Default %
        elif "absorbance" in st:
            self.cmb_signal_unit.addItem("Absorbance Units (AU / dimensionless)", "AU")
            self.cmb_signal_unit.addItem("dimensionless", "dimensionless")
            self.cmb_signal_unit.setCurrentIndex(1)
        elif "optical_depth" in st or "optical depth" in st:
            self.cmb_signal_unit.addItem("dimensionless", "dimensionless")
            self.cmb_signal_unit.setCurrentIndex(1)
        elif "cross" in st:
            self.cmb_signal_unit.addItem("cm^2/molecule", "cm^2/molecule")
            self.cmb_signal_unit.setCurrentIndex(1)

        self.cmb_signal_unit.blockSignals(False)

    def _on_apply(self) -> None:
        modality = self.cmb_modality.currentData()
        axis_unit = self.cmb_axis.currentData()
        signal_type = self.cmb_signal_type.currentData()
        signal_unit = self.cmb_signal_unit.currentData()
        notes = self.txt_notes.text().strip() or None

        try:
            attested = attest_observation_context(
                self.context,
                modality=modality,
                axis_unit=axis_unit,
                signal_type=signal_type,
                signal_unit=signal_unit,
                notes=notes,
            )
        except ValueError as exc:
            QMessageBox.warning(
                self,
                "Attestation Validation Failed",
                f"<b>Cannot apply attestation:</b><br><br>{exc}",
            )
            return

        self.attested_context = attested
        self.accept()

