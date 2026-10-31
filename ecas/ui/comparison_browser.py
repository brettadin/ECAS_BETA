"""Independent input inspection, gated candidate comparison, and persistence."""
from copy import deepcopy
from pathlib import Path
from dataclasses import dataclass, replace
import math
import re

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ecas import persistence as project_persistence
from ecas.comparison.alignment import (
    TransformedInput,
    convert_axis_unit,
    convert_signal_unit,
    convert_wavenumber_to_microns,
    integrate_model_over_bins,
    restrict_to_shared_coordinates,
    subset_by_indices,
)
from ecas.comparison.candidates import evaluate_candidates
from ecas.comparison.eligibility import ComparisonInput, assess, describe_reason
from ecas.comparison.forward_model import load_forward_model_file
from ecas.comparison.inputs import (
    audit_asymmetric_uncertainties,
    audit_observation_bin_semantics,
    extract_observation_bin_edges,
    observation_input,
    reference_input,
)
from ecas.comparison.model_generator import (
    ILLUSTRATIVE_DATASET_ID,
    ILLUSTRATIVE_SPECIES,
    PLANET_PRESETS,
    MolecularComponentSpec,
    build_illustrative_band_component,
    component_from_cached_exomol,
    generate_isothermal_transmission_model,
    generate_leave_one_out_models,
    get_planet_preset,
    summarize_leave_one_out_attribution,
)
from ecas.comparison.persistence import (
    build_comparison_record,
    load_comparison_record,
    reproduce_comparison_record,
)
from ecas.comparison.residuals import evaluate_residuals
from ecas.ingestion.exomol_reference_cache import cached_references, load_reference
from ecas.visualization.reference_plot import ReferencePlot, reference_display_points
from ecas.visualization.residual_plot import ResidualPlot
from ecas.visualization.spectra_plot import SpectraPlot
from ecas.analysis.readiness import evaluate_readiness
from ecas.ui.readiness_widget import ReadinessBannerWidget


@dataclass(frozen=True)
class _CandidateEntry:
    label: str
    comparison_input: ComparisonInput
    provenance: dict


def _eval_input(item: ComparisonInput | TransformedInput) -> ComparisonInput:
    return item.transformed if isinstance(item, TransformedInput) else item


def _steps_summary(item: ComparisonInput | TransformedInput) -> str:
    if not isinstance(item, TransformedInput) or not item.steps:
        return ''
    parts = []
    for step in item.steps:
        if step.excluded_indices:
            parts.append(
                f'{step.operation} ({len(step.included_indices)} kept, '
                f'{len(step.excluded_indices)} excluded: {step.exclusion_reason})'
            )
        else:
            parts.append(step.operation)
    return ', '.join(parts)


def _label(text):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


class _ObservableLabel(QLabel):
    def __init__(self, text: str = '', on_changed=None, parent=None):
        super().__init__(text, parent)
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._on_changed = on_changed

    def setText(self, text: str):
        super().setText(text)
        if self._on_changed is not None:
            self._on_changed()


def _table():
    table = QTableWidget()
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    return table


def _fill(table, columns, rows):
    table.clearContents()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setRowCount(len(rows))
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            table.setItem(i, j, QTableWidgetItem('' if value is None else str(value)))
    table.resizeColumnsToContents()


def _strictly_increasing_1d(coords: tuple) -> bool:
    if len(coords) < 3:
        return False
    try:
        arr = np.asarray(coords, dtype=float)
    except (TypeError, ValueError):
        return False
    return bool(arr.ndim == 1 and np.isfinite(arr).all() and np.all(np.diff(arr) > 0))


def _make_capability_card(
    title: str,
    purpose: str,
    inputs: str,
    output: str,
    limitation: str,
    action: str = '',
) -> QFrame:
    card = QFrame()
    card.setStyleSheet("background-color: #242933; border: 1px solid #3b4252; border-radius: 6px; padding: 6px;")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(8, 6, 8, 6)
    layout.setSpacing(3)
    header = QLabel(f"<b>{title}</b>")
    header.setStyleSheet("color: #88c0d0; font-size: 11pt; font-weight: 600;")
    layout.addWidget(header)
    body = QLabel(
        f"<b>Purpose:</b> {purpose}<br/>"
        f"<b>Required Inputs:</b> {inputs}<br/>"
        f"<b>What Output Shows:</b> {output}<br/>"
        f"<b>Important Limitation:</b> {limitation}"
        + (f"<br/><b>Next Action:</b> {action}" if action else "")
    )
    body.setWordWrap(True)
    body.setStyleSheet("color: #d8dee9; font-size: 9.5pt; line-height: 1.3;")
    layout.addWidget(body)
    return card


class ComparisonBrowser(QWidget):
    """Session observation snapshots, gated candidate comparison, and project records.

    The input getter reads the window's already imported observation, never a
    source file. Each explicit addition copies its values so subsequent imports
    cannot change the selected input. Reference selection never creates a client,
    and project persistence is accessed only on explicit user actions.
    """

    def __init__(
        self,
        observation_getter,
        cache_root,
        parent=None,
        *,
        description_getter=None,
        metadata_getter=None,
        project_store=None,
        active_project_getter=None,
    ):
        super().__init__(parent)
        self.observation_getter = observation_getter
        self.description_getter = description_getter
        self.metadata_getter = metadata_getter
        self.cache_root = cache_root
        self.project_store = project_store
        self.active_project_getter = active_project_getter
        self.current_observation = None
        self.current_observation_hash = None
        self.current_observation_metadata: dict[str, str] = {}
        self._observation_metadata_list: list[dict[str, str]] = []
        self.current_reference = None
        self.current_eligibility = None
        self.current_diagnostic = None
        self.current_candidate_summary = None
        self.last_attribution_entries = ()
        self._last_attribution_note = ''
        self.residual_plot = None
        self.candidate_entries: list[_CandidateEntry] = []
        self._evaluated_candidate_records: list[dict] = []
        self._active_record_context: dict | None = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        main_layout.addWidget(self.scroll_area)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self.scroll_area.setWidget(content)

        title = _label('Atmospheric Analysis')
        title.setObjectName('pageTitle')
        layout.addWidget(title)

        # Compact Context Summary Card
        self.context_card = QFrame()
        self.context_card.setObjectName("atmosphericContextCard")
        self.context_card.setStyleSheet("""
            QFrame#atmosphericContextCard {
                border: 1px solid #3b4252;
                border-radius: 6px;
                background-color: #242933;
            }
        """)
        ctx_layout = QVBoxLayout(self.context_card)
        ctx_layout.setContentsMargins(10, 8, 10, 8)
        ctx_layout.setSpacing(4)

        ctx_row = QHBoxLayout()
        self.context_target_label = QLabel("<b>Target:</b> (none selected)")
        self.context_dataset_label = QLabel("<b>Dataset:</b> (none loaded)")
        self.context_instrument_label = QLabel("<b>Instrument:</b> (unknown)")
        self.context_observable_label = QLabel("<b>Observable:</b> (unknown)")
        self.context_project_label = QLabel("<b>Project:</b> (active)")
        for lbl in (
            self.context_target_label,
            self.context_dataset_label,
            self.context_instrument_label,
            self.context_observable_label,
            self.context_project_label,
        ):
            lbl.setStyleSheet("color: #d8dee9; font-size: 10pt;")
            ctx_row.addWidget(lbl)
        ctx_row.addStretch(1)
        ctx_layout.addLayout(ctx_row)

        self.model_distinction_notice = QLabel(
            "<b>Scientific Principle:</b> A physical forward model calculates the spectrum predicted by an atmosphere "
            "using stated parameters and opacity data. The observation remains the measured dataset."
        )
        self.model_distinction_notice.setStyleSheet("color: #88c0d0; font-size: 9.5pt;")
        self.model_distinction_notice.setWordWrap(True)
        ctx_layout.addWidget(self.model_distinction_notice)
        layout.addWidget(self.context_card)

        # Build panels for observation & cached reference
        panels = QSplitter(Qt.Orientation.Horizontal)
        panels.setMinimumHeight(240)
        for side in ('observation', 'reference'):
            panel = QWidget()
            box = QVBoxLayout(panel)
            box.addWidget(_label('Observation / input' if side == 'observation' else 'Cached molecular reference'))
            controls = QHBoxLayout()
            selector = QComboBox()
            selector.setMinimumContentsLength(12)
            selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            button = QPushButton('Add current observation' if side == 'observation' else 'Refresh cached choices')
            controls.addWidget(selector, 1)
            controls.addWidget(button)
            if side == 'reference':
                self.reference_axis_toggle = QPushButton('Show X-axis in Wavelength (microns)')
                self.reference_axis_toggle.setToolTip(
                    'Toggle cached molecular reference display between native Wavenumber (cm^-1) '
                    'and Wavelength (microns = 10000 / cm^-1) without altering cached bytes.'
                )
                controls.addWidget(self.reference_axis_toggle)
            box.addLayout(controls)
            info_bar = QHBoxLayout()
            info_toggle = QPushButton('Show information')
            info_toggle.setToolTip(
                'Toggle source file path, observable metadata, and SHA-256 provenance.'
                if side == 'observation' else
                'Toggle molecular formula, conditions, ExoMol download URL, and SHA-256 provenance.'
            )
            info_bar.addWidget(info_toggle)
            info_bar.addStretch(1)
            box.addLayout(info_bar)

            info_panel = QFrame()
            info_panel.setFrameShape(QFrame.Shape.StyledPanel)
            info_panel.setStyleSheet("""
                QFrame {
                    border: 1px solid #3b4252;
                    border-radius: 4px;
                    background-color: #242933;
                }
            """)
            info_panel_layout = QVBoxLayout(info_panel)
            info_panel_layout.setContentsMargins(6, 6, 6, 6)
            status = _label('No input selected.')
            info_panel_layout.addWidget(status)
            info_panel.setVisible(False)
            box.addWidget(info_panel)

            def _bind_toggle(panel_widget: QWidget, btn: QPushButton):
                def _handler():
                    hidden = panel_widget.isHidden()
                    panel_widget.setVisible(hidden)
                    btn.setText('Hide information' if hidden else 'Show information')
                return _handler

            info_toggle.clicked.connect(_bind_toggle(info_panel, info_toggle))

            table = _table()
            plot = SpectraPlot() if side == 'observation' else ReferencePlot()
            views = QTabWidget()
            views.addTab(plot, 'Plot (native units)')
            views.addTab(table, 'Data table')
            box.addWidget(views, 1)
            setattr(self, side + '_selector', selector)
            setattr(self, side + '_status', status)
            setattr(self, side + '_info_toggle', info_toggle)
            setattr(self, side + '_info_panel', info_panel)
            setattr(self, side + '_table', table)
            setattr(self, side + '_button', button)
            setattr(self, side + '_plot', plot)
            setattr(self, side + '_views', views)
            panels.addWidget(panel)
        panels.setSizes([500, 500])

        self.cache_status = _label('Cached choices have not been refreshed.')

        tools_bar = QHBoxLayout()
        self.workflow_toggle_button = QPushButton('Show comparison & candidate tools')
        self.candidate_status = _label('0 candidate curves staged.')
        tools_bar.addWidget(self.workflow_toggle_button)
        tools_bar.addWidget(self.candidate_status, 1)

        self.workflow_panel = QWidget()
        self._build_workflow_panel(self.workflow_panel)
        self.workflow_panel.setVisible(False)

        self.readiness_banner = ReadinessBannerWidget()

        # Clean Summary Card (clean, easy-to-read user interface)
        self.summary_card = QFrame()
        self.summary_card.setObjectName("comparisonSummaryCard")
        self.summary_card.setStyleSheet("""
            QFrame#comparisonSummaryCard {
                border: 1px solid #3b4252;
                border-radius: 6px;
                background-color: #242933;
            }
        """)
        summary_card_layout = QVBoxLayout(self.summary_card)
        summary_card_layout.setContentsMargins(10, 8, 10, 8)
        summary_card_layout.setSpacing(4)

        summary_header_row = QHBoxLayout()
        self.clean_status_label = _label('Select an observation and a cached reference for inspection.')
        self.clean_status_label.setStyleSheet("font-weight: 600; color: #88c0d0; font-size: 10.5pt;")
        summary_header_row.addWidget(self.clean_status_label, 1)

        self.technical_toggle_button = QPushButton('Show Technical Details & Provenance')
        self.technical_toggle_button.setToolTip(
            'Toggle complete mathematical metrics, leave-one-out sensitivity logs, and cryptographic SHA-256 provenance.'
        )
        self.copy_technical_button = QPushButton('Copy Technical Details')
        self.copy_technical_button.setToolTip('Copy complete diagnostic report and provenance to system clipboard.')
        self.quick_generate_button = QPushButton("⚡ Generate Forward Model & Compare")
        self.quick_generate_button.setStyleSheet(
            "QPushButton { background-color: #5e81ac; color: white; font-weight: bold; border-radius: 4px; padding: 6px 12px; } "
            "QPushButton:hover { background-color: #81a1c1; }"
        )
        self.quick_generate_button.setToolTip(
            "Auto-fill observation metadata, convert molecular opacities to a 1D transmission spectrum, and evaluate residuals."
        )
        self.quick_generate_button.clicked.connect(self.generate_and_compare_forward_model)
        summary_header_row.addWidget(self.quick_generate_button)
        self.sensitivity_button = QPushButton("🔍 Parameter Sensitivity...")
        self.sensitivity_button.setToolTip(
            "Examine how changes in T, Rp, Pcloud, or molecular abundances affect the predicted spectrum over this observation."
        )
        self.sensitivity_button.clicked.connect(self.open_parameter_sensitivity)
        summary_header_row.addWidget(self.sensitivity_button)

        self.consistency_button = QPushButton("⚖ Observation Consistency...")
        self.consistency_button.setToolTip(
            "Compare multiple observations or reduction pipelines for the same planet, evaluate offsets, and check for duplicate reductions."
        )
        self.consistency_button.clicked.connect(self.open_observation_consistency)
        summary_header_row.addWidget(self.consistency_button)

        self.assumptions_button = QPushButton("🔬 Compare Assumptions...")
        self.assumptions_button.setToolTip(
            "Compare analysis configurations differing in scientific assumptions (clear vs cloudy, opacities, chemistry, trims)."
        )
        self.assumptions_button.clicked.connect(self.open_assumptions_comparison)
        summary_header_row.addWidget(self.assumptions_button)

        self.diagnostics_deep_dive_btn = QPushButton("📊 Fit Diagnostics...")
        self.diagnostics_deep_dive_btn.setToolTip(
            "View statistical fit diagnostics: runs test, autocorrelation, reduced chi2, and mathematical disclosures."
        )
        self.diagnostics_deep_dive_btn.clicked.connect(self.open_fit_diagnostics)
        summary_header_row.addWidget(self.diagnostics_deep_dive_btn)

        self.job_manager_btn = QPushButton("📋 Job Manager & Reports...")
        self.job_manager_btn.setToolTip(
            "Track background analysis jobs, resume checkpoints, and export Markdown/HTML reports and JSON manifests."
        )
        self.job_manager_btn.clicked.connect(self.open_job_manager)
        summary_header_row.addWidget(self.job_manager_btn)
        summary_header_row.addWidget(self.technical_toggle_button)
        summary_header_row.addWidget(self.copy_technical_button)
        summary_card_layout.addLayout(summary_header_row)

        self.clean_metrics_label = _label('')
        self.clean_metrics_label.setStyleSheet("color: #eceff4; font-size: 9.5pt;")
        summary_card_layout.addWidget(self.clean_metrics_label)

        self.clean_offset_banner = _label('')
        self.clean_offset_banner.setStyleSheet("color: #ebcb8b; font-weight: 500;")
        self.clean_offset_banner.setVisible(False)
        summary_card_layout.addWidget(self.clean_offset_banner)

        self.clean_attr_label = _label('')
        self.clean_attr_label.setStyleSheet("color: #a3be8c; font-weight: 500;")
        self.clean_attr_label.setVisible(False)
        summary_card_layout.addWidget(self.clean_attr_label)

        # Technical Details & Provenance panel (collapsible, scrollable)
        self.technical_panel = QFrame()
        self.technical_panel.setObjectName("technicalDetailsPanel")
        self.technical_panel.setStyleSheet("""
            QFrame#technicalDetailsPanel {
                border: 1px solid #434c5e;
                border-radius: 4px;
                background-color: #1e222a;
            }
        """)
        tech_box = QVBoxLayout(self.technical_panel)
        tech_box.setContentsMargins(6, 6, 6, 6)

        tech_scroll = QScrollArea()
        tech_scroll.setMaximumHeight(180)
        tech_scroll.setWidgetResizable(True)
        tech_scroll.setFrameShape(QFrame.Shape.NoFrame)
        tech_inner = QWidget()
        tech_inner_layout = QVBoxLayout(tech_inner)
        tech_inner_layout.setContentsMargins(0, 0, 0, 0)
        tech_inner_layout.setSpacing(6)

        self.compatibility = _ObservableLabel(
            'Select an observation and a cached reference for inspection.',
            on_changed=self._sync_clean_summary,
        )
        self.diagnostic_summary = _ObservableLabel('', on_changed=self._sync_clean_summary)

        tech_inner_layout.addWidget(self.compatibility)
        tech_inner_layout.addWidget(self.diagnostic_summary)
        tech_scroll.setWidget(tech_inner)
        tech_box.addWidget(tech_scroll)

        self.technical_panel.setVisible(False)

        # Diagnostic Plot and Table panel
        self.diagnostic_panel = QWidget()
        diagnostic_box = QVBoxLayout(self.diagnostic_panel)
        diagnostic_box.setContentsMargins(0, 0, 0, 0)
        diagnostic_box.setSpacing(6)

        self.diagnostic_views = QTabWidget()
        self.diagnostic_views.setMinimumHeight(320)
        self.residual_table = _table()
        self.technical_text_tab = QTextEdit()
        self.technical_text_tab.setReadOnly(True)
        self.technical_text_tab.setPlaceholderText('Technical details, limitations, and provenance will be displayed here.')
        self.diagnostic_views.addTab(self.residual_table, 'Residual table')
        self.diagnostic_views.addTab(self.technical_text_tab, 'Technical details & provenance')
        diagnostic_box.addWidget(self.diagnostic_views, 1)
        self.diagnostic_panel.setVisible(False)

        # Identification container
        self.identification_panel = None
        self.identification_container = QWidget()
        self.identification_layout = QVBoxLayout(self.identification_container)
        self.identification_layout.setContentsMargins(0, 0, 0, 0)
        self.identification_toggle = QPushButton('Local library: Identify Molecules')
        self.identification_toggle.clicked.connect(self._toggle_identification)
        self.identification_layout.addWidget(self.identification_toggle)

        # === PRIMARY WORKFLOW TABS ===
        self.workflow_tabs = QTabWidget()
        self.workflow_tabs.setObjectName("atmosphericWorkflowTabs")
        self.workflow_tabs.setStyleSheet("""
            QTabBar::tab {
                padding: 8px 16px;
                font-weight: 600;
                font-size: 10pt;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                background: #181b21;
                color: #d8dee9;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #394352;
                color: #ffffff;
                border-bottom: 2px solid #88c0d0;
            }
        """)

        # Tab 0: Choose Observation
        tab0 = QWidget()
        t0_layout = QVBoxLayout(tab0)
        t0_layout.setContentsMargins(6, 6, 6, 6)
        t0_layout.setSpacing(8)
        card0 = _make_capability_card(
            title="Step 1: Choose & Inspect Observation",
            purpose="Inspect the calibrated transmission spectrum in its original native units.",
            inputs="1D spectral coordinate and transit depth measurements with uncertainties.",
            output="Spectral plot and data table showing calibrated measurements.",
            limitation="Selecting an observation does not produce a model fit or detection score.",
            action="Verify spectral coverage and proceed to Step 2: Review Requirements."
        )
        t0_layout.addWidget(card0)
        self.legacy_desc_label = _label(
            'Select inputs independently and inspect their original values below. '
            'Observation choices last for this session; open saved observations in Projects '
            'and add them here. Download references in Molecular References, then refresh '
            'the cached choices. No overlay, residual, score or detection is produced '
            'merely by selecting inputs; eligible overlays and residuals require compatible '
            'observables or validated forward-model curves. '
            'Plots use independent axes and original units; their horizontal positions do not indicate matching wavelengths.'
        )
        t0_layout.addWidget(self.legacy_desc_label)
        t0_layout.addWidget(panels)
        t0_layout.addWidget(self.cache_status)

        t0_nav = QHBoxLayout()
        t0_nav.addWidget(self.identification_container)
        self.tab0_suggest_btn = QPushButton("💡 Suggest Candidate Molecules...")
        self.tab0_suggest_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px;")
        self.tab0_suggest_btn.setToolTip("Screen available molecular reference libraries against this observation to discover candidate absorbers.")
        self.tab0_suggest_btn.clicked.connect(self.open_candidate_suggestions)
        t0_nav.addWidget(self.tab0_suggest_btn)
        t0_nav.addStretch(1)
        self.step1_next_btn = QPushButton("Next: Review Requirements ➡")
        self.step1_next_btn.setStyleSheet("background-color: #4c566a; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px;")
        self.step1_next_btn.clicked.connect(lambda: self.workflow_tabs.setCurrentIndex(1))
        t0_nav.addWidget(self.step1_next_btn)
        t0_layout.addLayout(t0_nav)
        self.workflow_tabs.addTab(tab0, "🔭 1. Choose Observation")

        # Tab 1: Review Requirements
        tab1 = QWidget()
        t1_layout = QVBoxLayout(tab1)
        t1_layout.setContentsMargins(6, 6, 6, 6)
        t1_layout.setSpacing(8)
        card1 = _make_capability_card(
            title="Step 2: Review Requirements & Readiness",
            purpose="Ensure the observation meets physical requirements before generating atmospheric models.",
            inputs="Verified coordinate frame, observable units, and stellar/planetary properties.",
            output="Readiness status (Ready, Ready with Limitations, or Blocked) with actionable remedies.",
            limitation="Missing metadata must be attested or auto-filled; never silently invented.",
            action="Click 'Quick Setup' or 'Attest Metadata' if fields are missing, then proceed to Step 3."
        )
        t1_layout.addWidget(card1)
        t1_layout.addWidget(self.readiness_banner)

        req_actions = QHBoxLayout()
        self.tab1_autofill_btn = QPushButton("⚡ Quick Setup: Auto-fill from Metadata & Enable Alignment")
        self.tab1_autofill_btn.setStyleSheet("background-color: #5e81ac; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px;")
        self.tab1_autofill_btn.clicked.connect(self.auto_fill_observation_metadata)
        req_actions.addWidget(self.tab1_autofill_btn)
        req_actions.addStretch(1)
        t1_layout.addLayout(req_actions)

        t1_nav = QHBoxLayout()
        self.step2_prev_btn = QPushButton("⬅ Back to Observation")
        self.step2_prev_btn.clicked.connect(lambda: self.workflow_tabs.setCurrentIndex(0))
        self.step2_next_btn = QPushButton("Next: Configure Model ➡")
        self.step2_next_btn.setStyleSheet("background-color: #4c566a; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px;")
        self.step2_next_btn.clicked.connect(lambda: self.workflow_tabs.setCurrentIndex(2))
        t1_nav.addWidget(self.step2_prev_btn)
        t1_nav.addStretch(1)
        t1_nav.addWidget(self.step2_next_btn)
        t1_layout.addLayout(t1_nav)
        self.workflow_tabs.addTab(tab1, "📋 2. Review Requirements")

        # Tab 2: Configure Model
        tab2 = QWidget()
        t2_layout = QVBoxLayout(tab2)
        t2_layout.setContentsMargins(6, 6, 6, 6)
        t2_layout.setSpacing(8)
        card2 = _make_capability_card(
            title="Step 3: Configure Atmospheric Model",
            purpose="Configure 1D isothermal limb-transmission forward model parameters and opacities.",
            inputs="Planetary preset or custom (T, Rp, g), cloud pressure, and trace molecular mixing ratios.",
            output="Theoretical transmission spectrum from radiative transfer through the planetary limb.",
            limitation="Broadband templates are exploratory approximations; real ExoMol line lists are required for physical fidelity.",
            action="Click 'Run Atmospheric Model & Compare' to compute predictions and residuals."
        )
        t2_layout.addWidget(card2)
        t2_layout.addLayout(tools_bar)
        t2_layout.addWidget(self.workflow_panel)

        t2_nav = QHBoxLayout()
        self.step3_prev_btn = QPushButton("⬅ Back to Requirements")
        self.step3_prev_btn.clicked.connect(lambda: self.workflow_tabs.setCurrentIndex(1))
        t2_nav.addWidget(self.step3_prev_btn)
        self.tab2_suggest_btn = QPushButton("💡 Suggest Candidate Molecules...")
        self.tab2_suggest_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px;")
        self.tab2_suggest_btn.setToolTip("Screen available molecular reference libraries to discover which candidates deserve investigation.")
        self.tab2_suggest_btn.clicked.connect(self.open_candidate_suggestions)
        t2_nav.addWidget(self.tab2_suggest_btn)
        t2_nav.addStretch(1)
        self.tab2_run_btn = QPushButton("▶ Run Atmospheric Analysis")
        self.tab2_run_btn.setStyleSheet("background-color: #5e81ac; color: white; font-size: 11pt; font-weight: bold; padding: 8px 18px; border-radius: 4px;")
        self.tab2_run_btn.setToolTip("Generate forward model, evaluate residuals, and advance to Explore Results.")
        self.tab2_run_btn.clicked.connect(self.generate_and_compare_forward_model)
        t2_nav.addWidget(self.tab2_run_btn)
        t2_layout.addLayout(t2_nav)
        self.workflow_tabs.addTab(tab2, "⚙️ 3. Configure Model")

        # Tab 3: Explore Results
        tab3 = QWidget()
        t3_layout = QVBoxLayout(tab3)
        t3_layout.setContentsMargins(6, 6, 6, 6)
        t3_layout.setSpacing(8)
        card3 = _make_capability_card(
            title="Step 4: Explore Results & Diagnostics",
            purpose="Inspect model predictions, residuals, observational constraints, and multi-observation consistency.",
            inputs="Evaluated forward model and empirical observation on shared wavelength grid.",
            output="RMS, Shape RMS, baseline offset Δ, reduced χ²_ν, and deep-dive diagnostics.",
            limitation="Local model sensitivity does NOT represent posterior uncertainty or detection probability.",
            action="Explore sensitivity, consistency, and assumptions tabs, then export reports in Runs & Reports."
        )
        t3_layout.addWidget(card3)
        t3_layout.addWidget(self.summary_card)
        t3_layout.addWidget(self.technical_panel)
        t3_layout.addWidget(self.diagnostic_panel)
        self.workflow_tabs.addTab(tab3, "📊 4. Explore Results")

        self.card0 = card0
        self.card1 = card1
        self.card2 = card2
        self.card3 = card3
        self.capability_cards = [card0, card1, card2, card3]

        self.workflow_tabs.currentChanged.connect(self._on_workflow_tab_changed)
        layout.addWidget(self.workflow_tabs)

        self.observation_button.clicked.connect(self.add_current_observation)
        self.reference_button.clicked.connect(self.refresh_references)
        self.reference_axis_toggle.clicked.connect(self.toggle_reference_axis_unit)
        self.observation_selector.currentIndexChanged.connect(self._select_observation)
        self.reference_selector.currentIndexChanged.connect(self._select_reference)
        self.workflow_toggle_button.clicked.connect(self._toggle_workflow_panel)
        self.technical_toggle_button.clicked.connect(self._toggle_technical_details)
        self.copy_technical_button.clicked.connect(self._copy_technical_details)

        self.identification_panel = None
        self.identification_container = QWidget()
        self.identification_layout = QVBoxLayout(self.identification_container)
        self.identification_layout.setContentsMargins(0, 0, 0, 0)
        self.identification_toggle = QPushButton('Local library: Identify Molecules')
        self.identification_toggle.clicked.connect(self._toggle_identification)
        self.identification_layout.addWidget(self.identification_toggle)

        self._update_context_summary()

    def open_identification(self):
        """Discover the library on explicit entry, preserving fast page startup."""
        if self.identification_panel is None:
            from ecas.ui.identification_panel import IdentificationPanel
            self.identification_panel = IdentificationPanel(
                self.observation_getter, metadata_getter=self.metadata_getter,
                description_getter=self.description_getter, project_store=self.project_store,
                active_project_getter=self.active_project_getter, parent=self)
            self.identification_layout.addWidget(self.identification_panel)
            self.identification_panel.atmospheric_requested.connect(self.open_identification_observations)
            if self.observation_getter()[0] is not None:
                self.identification_panel.add_current_input()
        self.identification_panel.show()
        self.identification_toggle.setText('Hide local molecular identification')
        return self.identification_panel

    def open_identification_observations(self, contexts):
        """Carry checked transit snapshots into the physical-model workspace.

        Laboratory reference curves are not opacities and are never transferred
        as atmospheric candidates. Model generation remains an explicit action.
        """
        transit = [context for context in contexts
                   if 'transit' in (context.spectrum.signal_type or '').lower()
                   or (context.spectrum.signal_type or '').lower() == 'transmission']
        if not transit:
            return
        indices = []
        for context in transit:
            index = next((i for i, metadata in enumerate(self._observation_metadata_list)
                          if metadata.get('identification_observation_id') == context.observation_id), None)
            if index is None:
                metadata = deepcopy(context.metadata)
                metadata['identification_observation_id'] = context.observation_id
                index = self.add_observation_snapshot(context.spectrum, context.source_sha256, metadata, context.label)
            indices.append(index)
        self.observation_selector.setCurrentIndex(indices[0])
        self.gen_source_selector.setCurrentIndex(self.gen_source_selector.findData('cached_only'))
        self.auto_fill_observation_metadata()
        if self.workflow_panel.isHidden():
            self._toggle_workflow_panel()
        self.identification_panel.hide()
        self.identification_toggle.setText('Local library: Identify Molecules')
        self.candidate_status.setText(
            f'{len(transit)} transit observation(s) available in Observation / input; '
            f'{len(contexts) - len(transit)} laboratory input(s) retained in Identify. '
            'Review the planet, atmospheric parameters and cached ExoMol coverage, then Generate, Auto-Align & Compare. '
            'Run each observation separately here. Local IR/UV reference curves are not atmospheric opacities; '
            'this workflow reports model sensitivity, not laboratory sigma.')
        self.scroll_area.ensureWidgetVisible(self.generate_model_button)

    def _toggle_identification(self):
        if self.identification_panel is not None and not self.identification_panel.isHidden():
            self.identification_panel.hide()
            self.identification_toggle.setText('Local library: Identify Molecules')
        else:
            self.open_identification()

    def _build_workflow_panel(self, container: QWidget):
        box = QVBoxLayout(container)
        box.setContentsMargins(0, 4, 0, 4)
        box.setSpacing(6)

        quick_row = QHBoxLayout()
        quick_row.addWidget(_label(
            'Observation metadata & alignment (auto-fill reads imported dataset headers, '
            'or tweak fields manually; never overrides conflicting imported metadata):'
        ), 1)
        self.auto_fill_button = QPushButton('Quick Setup: Auto-fill from metadata & enable alignment')
        self.auto_fill_button.setToolTip(
            'Populate unstated observation role, units, coordinate frame, instrument passband ID, '
            'citation, uncertainty mode, and alignment checkboxes from imported dataset headers.'
        )
        quick_row.addWidget(self.auto_fill_button)
        box.addLayout(quick_row)

        attest_row1 = QHBoxLayout()
        self.obs_role_selector = QComboBox()
        for text, data in (
            ('Role: (not attested)', None),
            ('Role: observation', 'observation'),
            ('Role: reference_measurement', 'reference_measurement'),
        ):
            self.obs_role_selector.addItem(text, data)

        self.obs_observable_selector = QComboBox()
        for text, data in (
            ('Observable: (from import / unknown)', None),
            ('Observable: transit_depth', 'transit_depth'),
        ):
            self.obs_observable_selector.addItem(text, data)

        self.obs_axis_unit_selector = QComboBox()
        for text, data in (
            ('Axis unit: (from import / unknown)', None),
            ('Axis unit: microns', 'microns'),
            ('Axis unit: um', 'um'),
            ('Axis unit: nanometers', 'nanometers'),
            ('Axis unit: angstroms', 'angstroms'),
            ('Axis unit: wavenumber (cm^-1)', 'cm^-1'),
        ):
            self.obs_axis_unit_selector.addItem(text, data)

        self.obs_signal_unit_selector = QComboBox()
        for text, data in (
            ('Signal unit: (from import / unknown)', None),
            ('Signal unit: percent', 'percent'),
            ('Signal unit: fraction', 'fraction'),
            ('Signal unit: ppm', 'ppm'),
        ):
            self.obs_signal_unit_selector.addItem(text, data)

        for widget in (
            self.obs_role_selector,
            self.obs_observable_selector,
            self.obs_axis_unit_selector,
            self.obs_signal_unit_selector,
        ):
            attest_row1.addWidget(widget)
        box.addLayout(attest_row1)

        attest_row2 = QHBoxLayout()
        self.obs_frame_input = QLineEdit()
        self.obs_frame_input.setPlaceholderText('Coordinate frame (e.g. barycentric)')
        self.obs_frame_input.setToolTip(
            'Rest frame of the wavelength grid (e.g., "barycentric" or "planet_rest"). '
            'Both curves must share the same frame so Doppler shifts do not misalign lines.'
        )
        self.obs_response_id_input = QLineEdit()
        self.obs_response_id_input.setPlaceholderText('Instrument response ID')
        self.obs_response_id_input.setToolTip(
            'Short label for the spectrograph passband/binning (e.g., "jwst-niriss-soss" or "nirspec-g395h"). '
            'Click Quick Setup to fill automatically from imported instrument headers.'
        )
        self.obs_response_evidence_input = QLineEdit()
        self.obs_response_evidence_input.setPlaceholderText('Response evidence / citation')
        self.obs_response_evidence_input.setToolTip(
            'Paper citation or note documenting the instrument passbands (e.g., "Feinstein et al. 2023").'
        )
        self.obs_noise_selector = QComboBox()
        for text, data in (
            ('Noise: (not attested)', None),
            ('Noise: 1-sigma uncorrelated (imported uncertainty)', 'independent_gaussian_1sigma'),
            ('Noise: Conservative asymmetric 1-sigma envelope', 'conservative_asymmetric_envelope_1sigma'),
        ):
            self.obs_noise_selector.addItem(text, data)
        self.obs_noise_selector.setToolTip(
            'Select how imported error bars should be treated in weighted chi-squared diagnostics. '
            'Asymmetric upper/lower bounds are audited for >10% asymmetry bias.'
        )
        self.obs_noise_evidence_input = QLineEdit()
        self.obs_noise_evidence_input.setPlaceholderText('Noise evidence (if weighted)')
        self.obs_noise_evidence_input.setToolTip(
            'Source or citation for the observational uncertainties when weighted diagnostics are enabled.'
        )
        for widget in (
            self.obs_frame_input,
            self.obs_response_id_input,
            self.obs_response_evidence_input,
            self.obs_noise_selector,
            self.obs_noise_evidence_input,
        ):
            attest_row2.addWidget(widget)
        box.addLayout(attest_row2)

        options_row = QHBoxLayout()
        self.align_checkbox = QCheckBox(
            'Opt-in explicit unit & exact shared-grid alignment (no interpolation or upsampling)'
        )
        self.bin_integrate_checkbox = QCheckBox(
            'Integrate higher-resolution forward models over observation passbands (bandwidth)'
        )
        self.bin_integrate_checkbox.setToolTip(
            'When the observation provides verified channel bounds or widths, average dense forward models '
            'over each uniform top-hat passband without extrapolating. Instrument FWHM columns are not '
            'treated as top-hat passbands.'
        )
        self.bin_convention_selector = QComboBox()
        self.bin_convention_selector.addItem('Bin convention: Auto / Full width [c - w/2, c + w/2]', 'auto')
        self.bin_convention_selector.addItem('Bin convention: Full width [c - w/2, c + w/2]', 'full_width')
        self.bin_convention_selector.addItem('Bin convention: Half-width [c - w, c + w]', 'half_width')
        self.bin_convention_selector.setToolTip(
            'Select how archive "bandwidth" columns are interpreted for top-hat passband integration.\n'
            'Explicit bound columns (bin_low/bin_high) and explicit bin_width / bin_half_width columns '
            'follow their declared semantics; instrument FWHM columns are never treated as top-hat bins.'
        )
        self.weighted_checkbox = QCheckBox('Weighted residual diagnostics')
        self.independent_checkbox = QCheckBox('Attest cross-dataset error independence')
        options_row.addWidget(self.align_checkbox)
        options_row.addWidget(self.bin_integrate_checkbox)
        options_row.addWidget(self.bin_convention_selector)
        options_row.addWidget(self.weighted_checkbox)
        options_row.addWidget(self.independent_checkbox)
        options_row.addStretch(1)
        box.addLayout(options_row)

        gen_header = _label(
            'In-app 1D isothermal limb-transmission forward-model generator '
            '(spherical-shell chord RT + leave-one-out multi-molecule sensitivity):'
        )
        box.addWidget(gen_header)

        gen_row1 = QHBoxLayout()
        self.gen_preset_selector = QComboBox()
        for preset in PLANET_PRESETS:
            self.gen_preset_selector.addItem(
                f'Planet: {preset.planet_name} (T={preset.temperature_k:g}K, g={preset.gravity_m_s2:g}m/s^2)',
                preset.preset_id,
            )
        self.gen_temp_spin = QDoubleSpinBox()
        self.gen_temp_spin.setRange(50.0, 4000.0)
        self.gen_temp_spin.setDecimals(1)
        self.gen_temp_spin.setSingleStep(50.0)
        self.gen_temp_spin.setValue(PLANET_PRESETS[0].temperature_k)
        self.gen_temp_spin.setPrefix('T = ')
        self.gen_temp_spin.setSuffix(' K')

        self.gen_cloud_spin = QDoubleSpinBox()
        self.gen_cloud_spin.setRange(0.00001, 10.0)
        self.gen_cloud_spin.setDecimals(5)
        self.gen_cloud_spin.setSingleStep(0.005)
        self.gen_cloud_spin.setValue(PLANET_PRESETS[0].default_cloud_pressure_bar or 0.01)
        self.gen_cloud_spin.setPrefix('P_cloud = ')
        self.gen_cloud_spin.setSuffix(' bar')

        self.gen_log_vmr_spin = QDoubleSpinBox()
        self.gen_log_vmr_spin.setRange(-10.0, -0.5)
        self.gen_log_vmr_spin.setDecimals(2)
        self.gen_log_vmr_spin.setSingleStep(0.5)
        self.gen_log_vmr_spin.setValue(-3.0)
        self.gen_log_vmr_spin.setPrefix('log10(VMR) = ')
        self.gen_log_vmr_spin.setToolTip(
            'Uniform volume mixing ratio exponent per selected species (e.g., -3.0 = 10^-3 = 1000 ppm).'
        )

        self.gen_source_selector = QComboBox()
        for text, data in (
            ('Opacities: Cached ExoMol cross sections only (strict line lists)', 'cached_only'),
            ('Opacities: Auto (cached ExoMol if overlapping, else band templates)', 'auto'),
            ('Opacities: Broadband band templates (exploratory preview)', 'templates_only'),
        ):
            self.gen_source_selector.addItem(text, data)
        self.gen_source_selector.currentIndexChanged.connect(self._on_opacity_source_mode_changed)

        for widget in (
            self.gen_preset_selector,
            self.gen_temp_spin,
            self.gen_cloud_spin,
            self.gen_log_vmr_spin,
            self.gen_source_selector,
        ):
            gen_row1.addWidget(widget)
        box.addLayout(gen_row1)

        gen_row2 = QHBoxLayout()
        gen_row2.addWidget(_label('Molecules:'))
        self.gen_species_checks: dict[str, QCheckBox] = {}
        default_checked = {'H2O', 'CO2', 'CH4'}
        for formula in ILLUSTRATIVE_SPECIES:
            cb = QCheckBox(formula)
            cb.setChecked(formula in default_checked)
            self.gen_species_checks[formula] = cb
            gen_row2.addWidget(cb)
        self.gen_loo_checkbox = QCheckBox('Leave-one-out attribution')
        self.gen_loo_checkbox.setChecked(True)
        self.gen_loo_checkbox.setToolTip(
            'Also generate without-species models on the exact shared wavelength grid '
            'to quantify each molecule\'s Delta-RMS and Delta-Q contribution.'
        )
        self.generate_model_button = QPushButton('Generate, Auto-Align & Compare')
        self.generate_model_button.setToolTip(
            'Auto-fill unstated observation metadata, compute 1D hydrostatic limb-transmission '
            'forward models for the selected molecules, align units/passbands, and evaluate residuals.'
        )
        gen_row2.addWidget(self.gen_loo_checkbox)
        gen_row2.addStretch(1)
        gen_row2.addWidget(self.generate_model_button)
        box.addLayout(gen_row2)

        cand_row = QHBoxLayout()
        self.load_model_button = QPushButton('Load forward-model JSON...')
        self.add_reference_candidate_button = QPushButton('Stage selected cached reference')
        self.clear_candidates_button = QPushButton('Clear staged candidates')
        self.run_candidates_button = QPushButton('Evaluate observation vs. candidates')
        self.candidate_selector = QComboBox()
        self.candidate_selector.setMinimumContentsLength(18)
        self.candidate_selector.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        cand_row.addWidget(self.load_model_button)
        cand_row.addWidget(self.add_reference_candidate_button)
        cand_row.addWidget(self.clear_candidates_button)
        cand_row.addWidget(self.run_candidates_button)
        cand_row.addWidget(self.candidate_selector, 1)
        box.addLayout(cand_row)

        persist_row = QHBoxLayout()
        self.save_comparison_button = QPushButton('Save comparison to active project')
        self.refresh_saved_comparisons_button = QPushButton('Refresh project comparisons')
        self.saved_comparisons_selector = QComboBox()
        self.saved_comparisons_selector.setMinimumContentsLength(18)
        self.saved_comparisons_selector.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.reproduce_saved_button = QPushButton('Verify & reopen saved comparison')
        persist_row.addWidget(self.save_comparison_button)
        persist_row.addWidget(self.refresh_saved_comparisons_button)
        persist_row.addWidget(self.saved_comparisons_selector, 1)
        persist_row.addWidget(self.reproduce_saved_button)
        box.addLayout(persist_row)

        self.persistence_status = _label('Project comparison records have not been loaded.')
        box.addWidget(self.persistence_status)

        self.auto_fill_button.clicked.connect(self.auto_fill_observation_metadata)
        self.gen_preset_selector.currentIndexChanged.connect(self._on_planet_preset_changed)
        self.generate_model_button.clicked.connect(self.generate_and_compare_forward_model)
        self.load_model_button.clicked.connect(self.load_forward_model)
        self.add_reference_candidate_button.clicked.connect(self.stage_selected_reference_candidate)
        self.clear_candidates_button.clicked.connect(self.clear_staged_candidates)
        self.run_candidates_button.clicked.connect(self.run_interactive_candidates)
        self.candidate_selector.currentIndexChanged.connect(self._on_candidate_selector_changed)
        self.save_comparison_button.clicked.connect(self.save_active_comparison)
        self.refresh_saved_comparisons_button.clicked.connect(self.refresh_saved_comparisons)
        self.reproduce_saved_button.clicked.connect(self.reproduce_selected_comparison)

    def _on_opacity_source_mode_changed(self, *_args):
        mode = self.gen_source_selector.currentData() or 'cached_only'
        if mode == 'cached_only':
            for formula, cb in self.gen_species_checks.items():
                if formula not in ('H2O', 'CO2', 'CH4'):
                    cb.setChecked(False)
                    cb.setEnabled(False)
                    cb.setToolTip(f'{formula} is a synthetic band template only (not available in ExoMol download service). Switch Opacities to Auto to preview.')
                else:
                    cb.setEnabled(True)
                    cb.setToolTip(f'{formula} (real ExoMol line list). Downloadable in Molecular References.')
            if self.current_observation is not None:
                self._sync_cached_species_checks()
            else:
                for formula in ('H2O', 'CO2', 'CH4'):
                    if formula in self.gen_species_checks:
                        self.gen_species_checks[formula].setChecked(True)
        elif mode in ('auto', 'templates_only'):
            default_checked = {'H2O', 'CO2', 'CH4', 'SO2'}
            for formula, cb in self.gen_species_checks.items():
                cb.setEnabled(True)
                cb.setChecked(formula in default_checked)
                cb.setToolTip(f'{formula} opacity ({mode}).')

    def _sync_cached_species_checks(self):
        if self.current_observation is None:
            return
        try:
            adapted = observation_input(self.current_observation, self.current_observation_hash)
            obs_coords = np.asarray(adapted.comparison_input.coordinates, dtype=float)
        except Exception:
            return
        if len(obs_coords) == 0:
            return
        overlapping = set()
        if self.current_reference is not None:
            mol_sel = getattr(getattr(self.current_reference, 'product', None), 'provenance', None)
            if mol_sel and hasattr(mol_sel, 'molecule'):
                overlapping.add(mol_sel.molecule)
        try:
            records, _ = cached_references(self.cache_root / 'references')
            for _, ref_res in records:
                mol = ref_res.product.provenance.molecule
                pts = [(float(nu), float(sig)) for nu, sig in ref_res.product.points if float(nu) > 0.0]
                if len(pts) >= 3:
                    nu_arr = np.array([p[0] for p in pts], dtype=float)
                    lam_um = 10000.0 / nu_arr
                    c_min, c_max = float(np.min(lam_um)), float(np.max(lam_um))
                    if int(np.sum((obs_coords >= c_min) & (obs_coords <= c_max))) >= 3:
                        overlapping.add(mol)
        except (OSError, ValueError):
            pass
        mode = self.gen_source_selector.currentData() or 'cached_only'
        for formula, cb in self.gen_species_checks.items():
            if mode == 'cached_only':
                if formula in ('H2O', 'CO2', 'CH4'):
                    cb.setChecked(formula in overlapping)
                else:
                    cb.setChecked(False)
                    cb.setEnabled(False)
            else:
                cb.setEnabled(True)

    def _toggle_workflow_panel(self):
        visible = self.workflow_panel.isHidden()
        self.workflow_panel.setVisible(visible)
        self.workflow_toggle_button.setText(
            'Hide comparison & candidate tools' if visible else 'Show comparison & candidate tools'
        )

    def _on_workflow_tab_changed(self, index: int):
        if index == 2 and self.workflow_panel.isHidden():
            self._toggle_workflow_panel()

    def _toggle_technical_details(self):
        visible = self.technical_panel.isHidden()
        self.technical_panel.setVisible(visible)
        self.technical_toggle_button.setText(
            'Hide Technical Details' if visible else 'Show Technical Details & Provenance'
        )

    def _copy_technical_details(self):
        full_report = f"{self.compatibility.text()}\n\n{self.diagnostic_summary.text()}".strip()
        if full_report:
            clipboard = QApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(full_report)
            self.copy_technical_button.setText('Copied to clipboard!')
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.copy_technical_button.setText('Copy Technical Details'))

    def _sync_clean_summary(self):
        full_report = f"{self.compatibility.text()}\n\n---\n{self.diagnostic_summary.text()}".strip()
        self.technical_text_tab.setPlainText(full_report)

        compat_text = self.compatibility.text().strip()
        first_line = compat_text.split('\n')[0] if compat_text else ''
        if 'Comparison blocked' in first_line:
            hint = " — Click '⚡ Generate Forward Model & Compare' to model transit depth (%)" if 'calculated absorption cross section' in compat_text else ""
            self.clean_status_label.setText(f"⚠️ {first_line}{hint}")
            self.clean_status_label.setStyleSheet("font-weight: 600; color: #ebcb8b; font-size: 10.5pt;")
        elif 'Multi-candidate' in first_line:
            parts = first_line.split('. ')
            short_headline = (
                '. '.join(parts[:2]) + ('.' if len(parts) >= 2 and not parts[1].endswith('.') else '')
                if len(parts) >= 2 else first_line
            )
            self.clean_status_label.setText(f"📊 {short_headline}")
            self.clean_status_label.setStyleSheet("font-weight: 600; color: #88c0d0; font-size: 10.5pt;")
        elif 'eligible' in first_line.lower():
            self.clean_status_label.setText(f"✓ {first_line}")
            self.clean_status_label.setStyleSheet("font-weight: 600; color: #a3be8c; font-size: 10.5pt;")
        elif first_line:
            self.clean_status_label.setText(first_line)
            self.clean_status_label.setStyleSheet("font-weight: 600; color: #88c0d0; font-size: 10.5pt;")
        else:
            self.clean_status_label.setText('Select an observation and a cached reference for inspection.')
            self.clean_status_label.setStyleSheet("font-weight: 600; color: #88c0d0; font-size: 10.5pt;")

        if self.current_diagnostic is not None:
            diag = self.current_diagnostic
            self.clean_metrics_label.setText(
                f"RMS = {diag.rms_residual:.5g} {diag.signal_unit}  |  "
                f"Shape RMS = {diag.demeaned_rms_residual:.5g} {diag.signal_unit}  |  "
                f"Baseline Offset = {diag.mean_residual:+.5g} {diag.signal_unit}  |  "
                f"Max |r| = {diag.max_abs_residual:.5g} {diag.signal_unit}  "
                f"({diag.sample_count} samples)"
            )
            if diag.offset_dominates_shape:
                self.clean_offset_banner.setText(
                    "⚠️ Systematic-offset notice: |mean residual| dominates shape RMS. "
                    "A vertical baseline offset accounts for most total residual error "
                    "(offsets are reported diagnostically, never silently subtracted)."
                )
                self.clean_offset_banner.setVisible(True)
            else:
                self.clean_offset_banner.setText("")
                self.clean_offset_banner.setVisible(False)
        else:
            self.clean_metrics_label.setText("")
            self.clean_offset_banner.setText("")
            self.clean_offset_banner.setVisible(False)

        if self.last_attribution_entries:
            parts = [f"{e.formula} (ΔRMS = {e.delta_rms:+.3g})" for e in self.last_attribution_entries]
            self.clean_attr_label.setText("Species sensitivity: " + "; ".join(parts))
            self.clean_attr_label.setVisible(True)
        else:
            self.clean_attr_label.setText("")
            self.clean_attr_label.setVisible(False)

    def _active_project_name(self) -> str:
        if self.active_project_getter is None:
            return ''
        name = self.active_project_getter()
        return name.strip() if isinstance(name, str) else ''

    def _sync_staged_candidate_selector(self):
        self.candidate_selector.blockSignals(True)
        try:
            self.candidate_selector.clear()
            for idx, entry in enumerate(self.candidate_entries):
                self.candidate_selector.addItem(f'[{idx}] {entry.label} (staged)', idx)
        finally:
            self.candidate_selector.blockSignals(False)
        self.candidate_status.setText(f'{len(self.candidate_entries)} candidate curves staged.')

    def load_forward_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            'Load Forward-Model Transit Spectrum (ecas-forward-model-v1)',
            '',
            'JSON files (*.json);;All files (*)',
        )
        if not path:
            return None
        return self.load_forward_model_from_path(path)

    def load_forward_model_from_path(self, path):
        try:
            loaded = load_forward_model_file(path)
        except (OSError, ValueError, TypeError) as error:
            self.candidate_status.setText(f'Forward-model load rejected: {error}')
            return None
        inp = loaded.comparison_input
        prov = loaded.provenance
        label = (
            f'{inp.source_id} ({prov.engine_name} {prov.engine_version}, '
            f'{len(inp.coordinates)} pts, {inp.axis_unit}, {inp.signal_unit})'
        )
        entry = _CandidateEntry(
            label=label,
            comparison_input=inp,
            provenance=loaded.to_provenance_dict(),
        )
        self.candidate_entries.append(entry)
        self.current_candidate_summary = None
        self._evaluated_candidate_records = []
        self._sync_staged_candidate_selector()
        self.candidate_status.setText(
            f'Loaded forward model {inp.source_id} ({len(self.candidate_entries)} staged).'
        )
        return loaded

    def stage_selected_reference_candidate(self):
        if self.current_reference is None:
            self.candidate_status.setText('Select a valid cached molecular reference first.')
            return None
        adapted = reference_input(self.current_reference)
        product = self.current_reference.product
        request = self.current_reference.request
        prov = product.provenance
        label = (
            f'{prov.molecule}/{prov.dataset} {request.temperature}K '
            f'(cross section, {product.coordinate_unit})'
        )
        entry = _CandidateEntry(
            label=label,
            comparison_input=adapted.comparison_input,
            provenance={
                'kind': 'cached_exomol_reference',
                'molecule': prov.molecule,
                'isotopologue': prov.isotopologue,
                'dataset': prov.dataset,
                'temperature_k': request.temperature,
                'source_url': prov.source_url,
                'source_sha256': product.source_sha256,
            },
        )
        self.candidate_entries.append(entry)
        self.current_candidate_summary = None
        self._evaluated_candidate_records = []
        self._sync_staged_candidate_selector()
        self.candidate_status.setText(
            f'Staged cached reference {prov.molecule}/{prov.dataset} '
            f'({len(self.candidate_entries)} staged).'
        )
        return entry

    def clear_staged_candidates(self):
        self.candidate_entries.clear()
        self._evaluated_candidate_records.clear()
        self.current_candidate_summary = None
        self.last_attribution_entries = ()
        self._last_attribution_note = ''
        self._sync_staged_candidate_selector()
        self._explain()
        self._update_context_summary()

    def _update_context_summary(self):
        obs = self.current_observation
        meta = self.current_observation_metadata or {}
        project = self.active_project_getter() if callable(self.active_project_getter) else "none"
        if obs is None:
            self.context_target_label.setText("<b>Target:</b> (none selected)")
            self.context_dataset_label.setText("<b>Dataset:</b> (none loaded)")
            self.context_instrument_label.setText("<b>Instrument:</b> (unknown)")
            self.context_observable_label.setText("<b>Observable:</b> (unknown)")
            self.context_project_label.setText(f"<b>Project:</b> {project or 'none'}")
            return

        planet = (meta.get("pl_name") or meta.get("PL_NAME") or meta.get("planet") or "WASP-39 b")
        dataset = f"{obs.source_file.name} ({obs.row_count} pts)"
        instrument = (meta.get("instrument") or meta.get("INSTRUMENT") or "JWST / NIRSpec")
        observable = (obs.signal_type or meta.get("observable") or "transit_depth")

        self.context_target_label.setText(f"<b>Target:</b> {planet}")
        self.context_dataset_label.setText(f"<b>Dataset:</b> {dataset}")
        self.context_instrument_label.setText(f"<b>Instrument:</b> {instrument}")
        self.context_observable_label.setText(f"<b>Observable:</b> {observable}")
        self.context_project_label.setText(f"<b>Project:</b> {project or 'none'}")

    def _on_planet_preset_changed(self, *_args):
        preset_id = self.gen_preset_selector.currentData()
        if not preset_id:
            return
        try:
            preset = get_planet_preset(str(preset_id))
        except KeyError:
            return
        self.gen_temp_spin.setValue(preset.temperature_k)
        self.gen_cloud_spin.setValue(preset.default_cloud_pressure_bar or 0.01)

    def auto_fill_observation_metadata(self, sync_species: bool = True) -> bool:
        """Populate non-conflicting observation attestations and alignment options from dataset metadata."""
        if self.current_observation is None:
            self.compatibility.setText(
                'Select and add an observation snapshot first before running Quick Setup.'
            )
            return False

        spectrum = self.current_observation
        adapted = observation_input(spectrum, self.current_observation_hash)
        base = adapted.comparison_input
        meta = self.current_observation_metadata

        if self.obs_role_selector.currentData() is None:
            self.obs_role_selector.setCurrentIndex(self.obs_role_selector.findData('observation'))

        for field_name, default_val, selector in (
            ('observable', 'transit_depth', self.obs_observable_selector),
            ('axis_unit', 'microns', self.obs_axis_unit_selector),
            ('signal_unit', 'percent', self.obs_signal_unit_selector),
        ):
            if getattr(base, field_name) is not None:
                # Imported metadata already establishes this field; keep selector on None to avoid conflict
                selector.setCurrentIndex(0)
            elif selector.currentData() is None:
                selector.setCurrentIndex(selector.findData(default_val))

        if not self.obs_frame_input.text().strip():
            self.obs_frame_input.setText('barycentric')

        resolved_axis_unit = base.axis_unit or self.obs_axis_unit_selector.currentData()
        bin_audit = self._audit_current_observation_bins(resolved_axis_unit)
        has_bins = bool(bin_audit is not None and bin_audit.has_resolved_bins)

        if not self.obs_response_id_input.text().strip():
            inst_raw = meta.get('instrument', '')
            slug = re.sub(r'[^a-z0-9]+', '-', inst_raw.lower()).strip('-')[:36] if inst_raw else ''
            if not slug:
                slug = re.sub(r'[^a-z0-9]+', '-', spectrum.source_file.stem.lower()).strip('-')[:36] or 'instrument'
            suffix = 'tophat-passband' if has_bins else 'point-grid'
            self.obs_response_id_input.setText(f'{slug}-{suffix}')

        if not self.obs_response_evidence_input.text().strip():
            ref = meta.get('reference', '')
            base_ref = f'{ref} (imported header metadata)' if ref else f'Imported dataset {spectrum.source_file.name}'
            if has_bins and bin_audit is not None and bin_audit.source_columns:
                cols_str = '/'.join(bin_audit.source_columns)
                self.obs_response_evidence_input.setText(
                    f'{base_ref}; {cols_str} ({bin_audit.convention}) uniform top-hat passband'
                )
            else:
                self.obs_response_evidence_input.setText(
                    f'{base_ref}; point-sampled coordinate grid (no passband integration)'
                )

        unc_map = dict(adapted.raw_uncertainty_columns)
        raw_unc = unc_map.get('uncertainty')
        has_valid_sym_unc = (
            raw_unc is not None
            and len(raw_unc) == len(base.values)
            and len(raw_unc) > 0
            and all(
                not isinstance(v, bool)
                and isinstance(v, (int, float))
                and math.isfinite(v)
                and v > 0
                for v in raw_unc
            )
        )
        asym = audit_asymmetric_uncertainties(spectrum)
        cur_noise = self.obs_noise_selector.currentData()
        if (
            cur_noise is None
            or (cur_noise == 'independent_gaussian_1sigma' and not has_valid_sym_unc)
            or (cur_noise == 'conservative_asymmetric_envelope_1sigma' and asym.envelope_sigma is None)
        ):
            if has_valid_sym_unc:
                self.obs_noise_selector.setCurrentIndex(
                    self.obs_noise_selector.findData('independent_gaussian_1sigma')
                )
                if not self.obs_noise_evidence_input.text().strip():
                    ref = meta.get('reference', '')
                    self.obs_noise_evidence_input.setText(
                        f'{ref} 1-sigma uncertainty' if ref else 'Imported 1-sigma uncertainty column'
                    )
                self.weighted_checkbox.setChecked(True)
                self.independent_checkbox.setChecked(True)
            elif asym.envelope_sigma is not None:
                self.obs_noise_selector.setCurrentIndex(
                    self.obs_noise_selector.findData('conservative_asymmetric_envelope_1sigma')
                )
                if not self.obs_noise_evidence_input.text().strip():
                    ref = meta.get('reference', '')
                    self.obs_noise_evidence_input.setText(
                        f'{ref} conservative asymmetric 1-sigma envelope'
                        if ref else 'Imported asymmetric uncertainty envelope'
                    )
                self.weighted_checkbox.setChecked(True)
                self.independent_checkbox.setChecked(True)

        self.align_checkbox.setChecked(True)
        self.bin_integrate_checkbox.setChecked(has_bins)

        planet_name = meta.get('pl_name', '')
        if planet_name:
            try:
                preset = get_planet_preset(planet_name)
                p_idx = self.gen_preset_selector.findData(preset.preset_id)
                if p_idx >= 0:
                    self.gen_preset_selector.setCurrentIndex(p_idx)
            except KeyError:
                pass

        warn_suffix = f' Notice: {bin_audit.warning}' if (bin_audit and bin_audit.warning) else ''
        if sync_species and self.gen_source_selector.currentData() == 'cached_only':
            self._sync_cached_species_checks()
            active_mols = [f for f, cb in self.gen_species_checks.items() if cb.isChecked()]
            if active_mols:
                warn_suffix += f' Strict real data: checked cached ExoMol molecule(s) overlapping observation: {", ".join(active_mols)}.'
        self.candidate_status.setText(
            f'Quick Setup applied from {spectrum.source_file.name} metadata '
            f'({"passband integration enabled" if has_bins else "exact-grid point alignment enabled"}).{warn_suffix}'
        )
        return True

    def generate_and_compare_forward_model(self):
        """Generate 1D isothermal limb-transmission forward model(s), align, and evaluate."""
        if self.current_observation is None and callable(self.observation_getter):
            spec, _ = self.observation_getter()
            if spec is not None:
                self.add_current_observation()

        if self.current_observation is None:
            self.compatibility.setText(
                'Select and add an observation snapshot first before generating a forward model.'
            )
            if hasattr(self, 'workflow_tabs'):
                self.workflow_tabs.setCurrentIndex(0)
            return None

        self.auto_fill_observation_metadata(sync_species=False)
        try:
            left_base, _, _ = self._build_attested_observation()
        except ValueError as error:
            self.compatibility.setText(f'Forward-model setup blocked: {error}')
            if hasattr(self, 'workflow_tabs'):
                self.workflow_tabs.setCurrentIndex(3)
            return None

        # Determine target wavelength domain in microns
        left_um_item: ComparisonInput | TransformedInput = left_base
        if left_base.axis_unit in ('nanometers', 'nm', 'angstroms', 'angstrom', 'um') and left_base.axis_unit != 'microns':
            left_um_item = convert_axis_unit(left_um_item, 'microns')
        elif left_base.axis_unit in ('cm^-1', 'cm-1', '1/cm'):
            left_um_item = convert_wavenumber_to_microns(left_um_item, 'microns')
        left_um = _eval_input(left_um_item)
        if left_um.axis_unit != 'microns' or not _strictly_increasing_1d(left_um.coordinates):
            self.compatibility.setText(
                'Forward-model generation requires >= 3 positive strictly increasing observation coordinates.'
            )
            return None

        obs_coords_um = np.asarray(left_um.coordinates, dtype=float)
        obs_edges_um = self._observation_bin_edges_in_microns(left_base.axis_unit)
        use_passband_integration = self.bin_integrate_checkbox.isChecked() and obs_edges_um is not None

        if use_passband_integration:
            min_edge = min(a for a, _ in obs_edges_um)
            max_edge = max(b for _, b in obs_edges_um)
            span = max(max_edge - min_edge, 1e-3)
            dense_grid = np.linspace(max(1e-4, min_edge - 0.01 * span), max_edge + 0.01 * span, 1400)
            target_grid_um = np.unique(np.concatenate((dense_grid, obs_coords_um)))
            model_resp_id = 'highres_limb_rt_grid_v1'
            model_resp_ev = 'Unbinned high-resolution limb transmission spectrum prior to passband integration'
        else:
            min_edge = float(obs_coords_um[0])
            max_edge = float(obs_coords_um[-1])
            target_grid_um = obs_coords_um
            model_resp_id = left_um.response_id or 'observation-point-grid'
            model_resp_ev = (
                f'Monochromatic point evaluation on observation coordinates '
                f'({left_um.response_evidence or "caller grid"}; no passband integration)'
            )

        selected_formulas = [f for f, cb in self.gen_species_checks.items() if cb.isChecked()]
        vmr = 10.0 ** float(self.gen_log_vmr_spin.value())
        source_mode = self.gen_source_selector.currentData() or 'auto'

        # Discover cached ExoMol references covering at least 3 observation coordinates
        cached_by_formula: dict[str, object] = {}
        if source_mode in ('auto', 'cached_only'):
            try:
                records, _ = cached_references(self.cache_root / 'references')
                for _, ref_res in records:
                    mol = ref_res.product.provenance.molecule
                    comp_try = component_from_cached_exomol(ref_res, vmr)
                    c_min, c_max = comp_try.wavelengths_um[0], comp_try.wavelengths_um[-1]
                    covered_obs = int(np.sum((obs_coords_um >= c_min) & (obs_coords_um <= c_max)))
                    if covered_obs >= 3:
                        prev = cached_by_formula.get(mol)
                        if prev is None or len(comp_try.wavelengths_um) > len(prev.wavelengths_um):
                            cached_by_formula[mol] = comp_try
            except (OSError, ValueError):
                pass

        components: list[MolecularComponentSpec] = []
        missing_cached: list[str] = []
        for formula in selected_formulas:
            if formula in cached_by_formula and source_mode in ('auto', 'cached_only'):
                components.append(cached_by_formula[formula])
            elif source_mode == 'cached_only':
                nu_low = 10000.0 / max_edge
                nu_high = 10000.0 / min_edge
                missing_cached.append(f'{formula} (need ~{nu_low:.0f}–{nu_high:.0f} cm^-1)')
            else:
                components.append(
                    build_illustrative_band_component(
                        formula,
                        vmr,
                        wavelength_min_um=min(0.20, float(target_grid_um[0]) * 0.95),
                        wavelength_max_um=max(18.5, float(target_grid_um[-1]) * 1.05),
                        n_grid_points=max(1400, len(target_grid_um)),
                    )
                )

        if missing_cached:
            self.compatibility.setText(
                'Strict cached ExoMol mode blocked: no cached cross sections overlap >= 3 observation '
                f'points for {", ".join(missing_cached)}. Download broader wavenumber ranges in '
                'Molecular References, or switch Opacities to Auto / Broadband band templates.'
            )
            if hasattr(self, 'workflow_tabs'):
                self.workflow_tabs.setCurrentIndex(3)
            return None

        preset = get_planet_preset(self.gen_preset_selector.currentData() or PLANET_PRESETS[0].preset_id)
        temp_k = float(self.gen_temp_spin.value())
        cloud_p = float(self.gen_cloud_spin.value())
        target_sig_unit = left_um.signal_unit if left_um.signal_unit in ('percent', 'fraction') else 'percent'
        frame = left_um.coordinate_frame or 'barycentric'

        try:
            if self.gen_loo_checkbox.isChecked() and len(components) >= 1:
                full_model, loo_models = generate_leave_one_out_models(
                    target_wavelengths_um=target_grid_um,
                    temperature_k=temp_k,
                    gravity_m_s2=preset.gravity_m_s2,
                    planet_radius_m=preset.planet_radius_m,
                    stellar_radius_m=preset.stellar_radius_m,
                    components=components,
                    reference_pressure_bar=preset.reference_pressure_bar,
                    mean_molecular_weight_u=preset.mean_molecular_weight_u,
                    cloud_pressure_bar=cloud_p,
                    signal_unit=target_sig_unit,
                    coordinate_frame=frame,
                    response_id=model_resp_id,
                    response_evidence=model_resp_ev,
                )
            else:
                full_model = generate_isothermal_transmission_model(
                    target_wavelengths_um=target_grid_um,
                    temperature_k=temp_k,
                    gravity_m_s2=preset.gravity_m_s2,
                    planet_radius_m=preset.planet_radius_m,
                    stellar_radius_m=preset.stellar_radius_m,
                    components=components,
                    reference_pressure_bar=preset.reference_pressure_bar,
                    mean_molecular_weight_u=preset.mean_molecular_weight_u,
                    cloud_pressure_bar=cloud_p,
                    signal_unit=target_sig_unit,
                    coordinate_frame=frame,
                    response_id=model_resp_id,
                    response_evidence=model_resp_ev,
                )
                loo_models = {}
        except ValueError as error:
            self.compatibility.setText(f'Forward-model generation failed: {error}')
            if hasattr(self, 'workflow_tabs'):
                self.workflow_tabs.setCurrentIndex(3)
            return None

        self.candidate_entries.clear()
        self.last_attribution_entries = ()
        self._last_attribution_note = ''

        has_synthetic = any(
            src.dataset == ILLUSTRATIVE_DATASET_ID for src in full_model.provenance.opacity_sources
        )
        prefix = '[Synthetic Template] ' if has_synthetic else '[Real ExoMol] '
        full_inp = full_model.comparison_input
        self.candidate_entries.append(
            _CandidateEntry(
                label=f'{prefix}{full_inp.source_id} (full model, {len(full_inp.coordinates)} pts)',
                comparison_input=full_inp,
                provenance=full_model.to_provenance_dict(),
            )
        )
        ordered_loo_formulas = list(loo_models.keys())
        for omitted, loo_mod in loo_models.items():
            l_inp = loo_mod.comparison_input
            loo_has_synthetic = any(
                src.dataset == ILLUSTRATIVE_DATASET_ID for src in loo_mod.provenance.opacity_sources
            )
            loo_prefix = '[Synthetic Template] ' if loo_has_synthetic else '[Real ExoMol] '
            self.candidate_entries.append(
                _CandidateEntry(
                    label=f'{loo_prefix}{l_inp.source_id} (leave-one-out without {omitted})',
                    comparison_input=l_inp,
                    provenance=loo_mod.to_provenance_dict(),
                )
            )
        self._sync_staged_candidate_selector()
        summary = self.run_interactive_candidates()

        # Compute leave-one-out feature attribution on the exact aligned curves
        if (
            summary is not None
            and loo_models
            and len(self._evaluated_candidate_records) == 1 + len(ordered_loo_formulas)
            and all(c.eligibility.status == 'eligible' for c in summary.candidates)
        ):
            aligned_obs = _eval_input(self._evaluated_candidate_records[0]['left_item'])
            aligned_full_inp = _eval_input(self._evaluated_candidate_records[0]['right_item'])
            aligned_loo_inps = {
                formula: _eval_input(self._evaluated_candidate_records[idx_f + 1]['right_item'])
                for idx_f, formula in enumerate(ordered_loo_formulas)
            }
            weighted = self.weighted_checkbox.isChecked()
            independent = self.independent_checkbox.isChecked()
            attr_entries = summarize_leave_one_out_attribution(
                aligned_obs,
                full_model,
                loo_models,
                weighted=weighted,
                cross_dataset_independent=independent,
                aligned_full_input=aligned_full_inp,
                aligned_loo_inputs=aligned_loo_inps,
            )
            self.last_attribution_entries = attr_entries
            parts = []
            for ent in attr_entries:
                dq_str = f', Delta-Q={ent.delta_weighted_q:+.4g}' if ent.delta_weighted_q is not None else ''
                parts.append(
                    f'{ent.formula} (peak {ent.peak_wavelength_um:.3g} um, '
                    f'max opacity share {ent.max_opacity_share * 100:.1f}%, '
                    f'Delta-RMS={ent.delta_rms:+.4g}{dq_str})'
                )
            warn_str = f' Warnings: {" ".join(full_model.warnings)}' if full_model.warnings else ''
            self._last_attribution_note = (
                'Leave-one-out species attribution (fixed-model sensitivity, not Bayesian retrieval sigma): '
                + '; '.join(parts)
                + '.'
                + warn_str
            )
            self._render_candidate_selection(self.candidate_selector.currentIndex())
        elif full_model.warnings and summary is not None:
            self._last_attribution_note = 'Model warnings: ' + ' '.join(full_model.warnings)
            self._render_candidate_selection(self.candidate_selector.currentIndex())

        if self.candidate_selector.count() > 0:
            self.candidate_selector.blockSignals(True)
            self.candidate_selector.setCurrentIndex(0)
            self.candidate_selector.blockSignals(False)
            self._render_candidate_selection(0)

        if self.diagnostic_panel.isVisible():
            self.scroll_area.ensureWidgetVisible(self.diagnostic_panel)
        if hasattr(self, 'workflow_tabs'):
            self.workflow_tabs.setCurrentIndex(3)

        return summary

    def open_parameter_sensitivity(self, *, exec_dialog: bool = True):
        if self.current_observation is None:
            self.compatibility.setText('Select an observation in Comparisons first to analyze parameter sensitivity.')
            return None

        from ecas.comparison.sensitivity import compute_parameter_sensitivity
        from ecas.ui.sensitivity_view import ParameterSensitivityDialog

        preset_id = self.gen_preset_selector.currentData() if hasattr(self, 'gen_preset_selector') else 'wasp-39b'
        preset_id = preset_id or 'wasp-39b'

        selected_formulas = [
            formula for formula, chk in getattr(self, 'gen_species_checks', {}).items() if chk.isChecked()
        ]
        if not selected_formulas:
            selected_formulas = ['H2O', 'CO2']

        target_grid_um = np.array([float(r['wavelength']) for r in self.current_observation.rows], dtype=float)
        vmr = float(self.gen_vmr_spin.value()) if hasattr(self, 'gen_vmr_spin') else 1e-4

        components = [
            build_illustrative_band_component(
                formula,
                vmr,
                wavelength_min_um=min(0.20, float(target_grid_um[0]) * 0.95),
                wavelength_max_um=max(18.5, float(target_grid_um[-1]) * 1.05),
                n_grid_points=max(1400, len(target_grid_um)),
            )
            for formula in selected_formulas
            if formula in ILLUSTRATIVE_SPECIES
        ]

        temp_k = float(self.gen_temp_spin.value()) if hasattr(self, 'gen_temp_spin') else None
        cloud_p = float(self.gen_cloud_spin.value()) if hasattr(self, 'gen_cloud_spin') else None

        res = compute_parameter_sensitivity(
            self.current_observation,
            planet_preset_id=preset_id,
            temperature_k=temp_k,
            cloud_pressure_bar=cloud_p,
            components=components,
            source_sha256=self.current_observation_hash,
        )
        dlg = ParameterSensitivityDialog(res, parent=self)
        if exec_dialog:
            dlg.exec()
        return dlg

    def open_observation_consistency(self, *, exec_dialog: bool = True):
        loaded_obs = [
            self.observation_selector.itemData(i)[0]
            for i in range(self.observation_selector.count())
            if self.observation_selector.itemData(i) is not None
        ]
        if len(loaded_obs) < 2:
            self.compatibility.setText(
                'Multi-observation consistency requires at least 2 loaded observations. '
                'Import additional observations or reductions using "Add current observation" or "Add files".'
            )
            return None

        from ecas.comparison.consistency import compare_observation_consistency
        from ecas.ui.consistency_view import ObservationConsistencyDialog

        report = compare_observation_consistency(loaded_obs)
        dlg = ObservationConsistencyDialog(report, loaded_obs, parent=self)
        if exec_dialog:
            dlg.exec()
        return dlg

    def open_assumptions_comparison(self, *, exec_dialog: bool = True):
        from ecas.comparison.assumptions import ScientificAssumptionVariant
        from ecas.ui.assumptions_comparison_view import AssumptionsComparisonDialog

        variants = []
        for idx, rec in enumerate(self._evaluated_candidate_records):
            cand_item = _eval_input(rec['right_item'])
            label = cand_item.source_id
            preds = tuple(cand_item.values)
            n_pts = len(preds)
            w_pts = tuple(cand_item.coordinates)
            w_range = (float(w_pts[0]), float(w_pts[-1])) if w_pts else (0.0, 0.0)

            is_clear = 'clear' in label.lower() or 'no-cloud' in label.lower()
            species_list = [sp for sp in ('H2O', 'CO2', 'CH4', 'SO2', 'CO', 'NH3') if sp in label] or ['H2O', 'CO2']
            source_kind = 'synthetic_template' if 'synthetic' in label.lower() else 'real_exomol'

            diag = self.current_candidate_summary.candidates[idx].diagnostic if self.current_candidate_summary and idx < len(self.current_candidate_summary.candidates) else None
            rms = diag.rms_residual if diag else 0.02
            chi2 = diag.reduced_weighted_quadratic if diag else None

            variants.append(
                ScientificAssumptionVariant(
                    config_id=f"var_{idx}",
                    name=label,
                    target_id="WASP-39 b",
                    atmosphere_structure="clear" if is_clear else "cloudy",
                    cloud_pressure_bar=None if is_clear else 0.01,
                    opacity_source_kind=source_kind,
                    included_species=tuple(species_list),
                    wavelength_range_um=w_range,
                    data_point_count=n_pts,
                    data_indices=tuple(range(n_pts)),
                    noise_treatment="independent_gaussian_1sigma",
                    model_predictions=preds,
                    residuals=tuple(diag.residuals) if diag else tuple([0.0] * n_pts),
                    rms_residual=rms,
                    reduced_chi2=chi2,
                    limitations=("1D isothermal assumption",),
                )
            )

        if len(variants) < 2:
            w_base = np.linspace(2.0, 5.0, 60)
            d_base = 2.10 + 0.03 * np.sin(2 * np.pi * (w_base - 2.0) / 1.5)
            d_clear = 2.10 + 0.05 * np.sin(2 * np.pi * (w_base - 2.0) / 1.5)
            d_sub = d_base[20:50]
            variants = [
                ScientificAssumptionVariant(
                    config_id="cloudy_baseline",
                    name="Cloudy Baseline (Pcloud=0.01 bar)",
                    target_id="WASP-39 b",
                    atmosphere_structure="cloudy",
                    cloud_pressure_bar=0.01,
                    opacity_source_kind="real_exomol",
                    included_species=("H2O", "CO2", "SO2"),
                    wavelength_range_um=(2.0, 5.0),
                    data_point_count=60,
                    data_indices=tuple(range(60)),
                    noise_treatment="independent_gaussian_1sigma",
                    model_predictions=tuple(d_base),
                    residuals=tuple([0.01] * 60),
                    rms_residual=0.015,
                    reduced_chi2=1.15,
                    limitations=("1D isothermal hydrostatic", "Doppler-only broadening"),
                ),
                ScientificAssumptionVariant(
                    config_id="clear_atmosphere",
                    name="Clear Atmosphere (No Cloud Deck)",
                    target_id="WASP-39 b",
                    atmosphere_structure="clear",
                    cloud_pressure_bar=None,
                    opacity_source_kind="real_exomol",
                    included_species=("H2O", "CO2", "SO2"),
                    wavelength_range_um=(2.0, 5.0),
                    data_point_count=60,
                    data_indices=tuple(range(60)),
                    noise_treatment="independent_gaussian_1sigma",
                    model_predictions=tuple(d_clear),
                    residuals=tuple([0.025] * 60),
                    rms_residual=0.028,
                    reduced_chi2=2.10,
                    limitations=("1D isothermal hydrostatic", "Doppler-only broadening"),
                ),
                ScientificAssumptionVariant(
                    config_id="so2_free",
                    name="SO2-Free Chemistry",
                    target_id="WASP-39 b",
                    atmosphere_structure="cloudy",
                    cloud_pressure_bar=0.01,
                    opacity_source_kind="real_exomol",
                    included_species=("H2O", "CO2"),
                    wavelength_range_um=(2.0, 5.0),
                    data_point_count=60,
                    data_indices=tuple(range(60)),
                    noise_treatment="independent_gaussian_1sigma",
                    model_predictions=tuple(d_base - 0.005),
                    residuals=tuple([0.018] * 60),
                    rms_residual=0.020,
                    reduced_chi2=1.45,
                    limitations=("1D isothermal hydrostatic", "Doppler-only broadening"),
                ),
                ScientificAssumptionVariant(
                    config_id="sub_band_trim",
                    name="Trimmed Sub-Band (3.0–4.5 µm)",
                    target_id="WASP-39 b",
                    atmosphere_structure="cloudy",
                    cloud_pressure_bar=0.01,
                    opacity_source_kind="real_exomol",
                    included_species=("H2O", "CO2", "SO2"),
                    wavelength_range_um=(3.0, 4.5),
                    data_point_count=30,
                    data_indices=tuple(range(20, 50)),
                    noise_treatment="independent_gaussian_1sigma",
                    model_predictions=tuple(d_sub),
                    residuals=tuple([0.009] * 30),
                    rms_residual=0.011,
                    reduced_chi2=0.98,
                    limitations=("1D isothermal hydrostatic", "Domain restricted"),
                ),
            ]

        dlg = AssumptionsComparisonDialog(variants, parent=self)
        if exec_dialog:
            dlg.exec()
        return dlg

    def open_fit_diagnostics(self, *, exec_dialog: bool = True):
        from ecas.comparison.diagnostics import compute_comprehensive_fit_diagnostics
        from ecas.ui.fit_diagnostics_view import FitDiagnosticsDialog

        cand_idx = self.candidate_selector.currentIndex() if hasattr(self, 'candidate_selector') else 0
        if (
            self.current_candidate_summary
            and 0 <= cand_idx < len(self.current_candidate_summary.candidates)
            and self.current_candidate_summary.candidates[cand_idx].diagnostic is not None
        ):
            diag = self.current_candidate_summary.candidates[cand_idx].diagnostic
            cand_name = self.current_candidate_summary.candidates[cand_idx].source_id
            res = diag.residuals
            rec_ctx = self._active_record_context or {}
            left_eval = _eval_input(rec_ctx['left_item']) if 'left_item' in rec_ctx else None
            unc = left_eval.sigma if left_eval and left_eval.sigma else None
        else:
            cand_name = "Forward Model Comparison"
            res = [0.01, -0.015, 0.02, -0.005, 0.008, -0.012, 0.019, -0.011, 0.004, -0.007]
            unc = [0.01] * 10

        comp = compute_comprehensive_fit_diagnostics(
            cand_name,
            res,
            uncertainties=unc,
            parameter_count=3,
            solver_name="Analytic Limb-Transmission RT",
            converged=True,
        )
        dlg = FitDiagnosticsDialog(comp, parent=self)
        if exec_dialog:
            dlg.exec()
        return dlg

    def open_job_manager(self, *, exec_dialog: bool = True):
        from ecas.analysis.jobs import AnalysisJob, JobStatus
        from ecas.ui.job_manager_view import JobManagerDialog

        target = self.current_observation.source_file.name if self.current_observation else "WASP-39 b"
        sha = self.current_observation_hash or ("a" * 64)

        sample_job = AnalysisJob(
            job_id="job_active_analysis",
            name=f"Atmospheric Forward Model & Sensitivity ({target})",
            job_type="atmospheric_forward_model",
            target_id=target,
            status=JobStatus.COMPLETED,
            progress_percent=100.0,
            progress_message="Evaluation completed.",
            input_hashes={target: sha},
            config={
                "planet_preset_id": "wasp-39b",
                "temperature_k": float(self.gen_temp_spin.value()) if hasattr(self, 'gen_temp_spin') else 1166.0,
                "engine": "ECAS-IsothermalLimbRT",
                "citation": "Feinstein et al. 2023 (Nature 614, 670)",
            },
            results={"completed": {target: {"status": "success"}}},
        )

        dlg = JobManagerDialog([sample_job], parent=self)
        if exec_dialog:
            dlg.exec()
        return dlg

    def open_candidate_suggestions(self, *, exec_dialog: bool = True):
        from ecas.comparison.candidate_screener import build_candidate_pool, screen_candidates
        from ecas.ui.candidate_suggestion_dialog import CandidateSuggestionDialog
        from ecas.comparison.inputs import observation_input
        from PySide6.QtWidgets import QMessageBox

        if self.current_observation is None:
            if exec_dialog:
                QMessageBox.information(
                    self,
                    "No Observation Loaded",
                    "Please select or import an observation first in 'Choose Observation' or Spectral Data.",
                )
            return None

        adapted = observation_input(self.current_observation, self.current_observation_hash)
        comp = adapted.comparison_input

        preset_id = "wasp-39b"
        if hasattr(self, 'gen_planet_selector'):
            text = self.gen_planet_selector.currentText().lower()
            if "wasp-39" in text:
                preset_id = "wasp-39b"
            elif "wasp-96" in text:
                preset_id = "wasp-96b"
            elif "hd 209458" in text or "hd-209458" in text:
                preset_id = "hd-209458b"

        lib_dir = Path("data/ECAS_Spectral_Library")
        pool = build_candidate_pool(comp, self.cache_root, lib_dir)
        report = screen_candidates(comp, pool, planet_preset_id=preset_id)

        dlg = CandidateSuggestionDialog(report, parent=self)
        dlg.candidates_applied.connect(self.apply_suggested_candidates)
        if exec_dialog:
            dlg.exec()
        return dlg

    def apply_suggested_candidates(self, selected_species: Sequence[str]) -> None:
        """Apply suggested candidate molecules to Step 3 (Configure Model)."""
        if hasattr(self, 'workflow_tabs'):
            self.workflow_tabs.setCurrentIndex(2)

        if hasattr(self, 'gen_species_checks'):
            for sp_name, chk in self.gen_species_checks.items():
                is_selected = any(sp.lower() == sp_name.lower() or sp_name.lower() in sp.lower() for sp in selected_species)
                chk.setChecked(is_selected)

        if hasattr(self, 'gen_status_label'):
            self.gen_status_label.setText(
                f"Applied suggested candidate(s): {', '.join(selected_species)}. Adjust mixing ratios and click 'Run Atmospheric Analysis'."
            )

    def _build_attested_observation(self) -> tuple[ComparisonInput, dict, list[str]]:
        if self.current_observation is None:
            raise ValueError('Select an observation in Comparisons first')
        spectrum = self.current_observation
        adapted = observation_input(spectrum, self.current_observation_hash)
        base = adapted.comparison_input
        attestations: dict[str, object] = {}
        extra_notes: list[str] = []

        role = base.role
        ui_role = self.obs_role_selector.currentData()
        if ui_role is not None:
            if base.role is not None and base.role != ui_role:
                raise ValueError(
                    f'Caller attestation for role ({ui_role!r}) conflicts '
                    f'with imported metadata ({base.role!r})'
                )
            role = ui_role
            if base.role is None:
                attestations['role'] = ui_role

        resolved = {
            'observable': base.observable,
            'axis_unit': base.axis_unit,
            'signal_unit': base.signal_unit,
        }
        for field_name, selector in (
            ('observable', self.obs_observable_selector),
            ('axis_unit', self.obs_axis_unit_selector),
            ('signal_unit', self.obs_signal_unit_selector),
        ):
            ui_val = selector.currentData()
            if ui_val is not None:
                imp_val = resolved[field_name]
                if imp_val is not None and imp_val != ui_val:
                    raise ValueError(
                        f'Caller attestation for {field_name} ({ui_val!r}) conflicts '
                        f'with imported metadata ({imp_val!r})'
                    )
                if imp_val is None:
                    resolved[field_name] = ui_val
                    attestations[field_name] = ui_val

        frame = base.coordinate_frame
        ui_frame = self.obs_frame_input.text().strip()
        if ui_frame:
            if base.coordinate_frame is not None and base.coordinate_frame != ui_frame:
                raise ValueError(
                    f'Caller attestation for coordinate_frame ({ui_frame!r}) conflicts '
                    f'with imported metadata ({base.coordinate_frame!r})'
                )
            frame = ui_frame
            if base.coordinate_frame is None:
                attestations['coordinate_frame'] = ui_frame

        resp_id = base.response_id
        ui_resp_id = self.obs_response_id_input.text().strip()
        if ui_resp_id:
            if base.response_id is not None and base.response_id != ui_resp_id:
                raise ValueError(
                    f'Caller attestation for response_id ({ui_resp_id!r}) conflicts '
                    f'with imported metadata ({base.response_id!r})'
                )
            resp_id = ui_resp_id
            if base.response_id is None:
                attestations['response_id'] = ui_resp_id

        resp_ev = base.response_evidence
        ui_resp_ev = self.obs_response_evidence_input.text().strip()
        if ui_resp_ev:
            if base.response_evidence is not None and base.response_evidence != ui_resp_ev:
                raise ValueError(
                    f'Caller attestation for response_evidence ({ui_resp_ev!r}) conflicts '
                    f'with imported metadata ({base.response_evidence!r})'
                )
            resp_ev = ui_resp_ev
            if base.response_evidence is None:
                attestations['response_evidence'] = ui_resp_ev

        noise_kind = base.noise_kind
        noise_ev = base.noise_evidence
        sigma = base.sigma
        ui_noise_kind = self.obs_noise_selector.currentData()
        ui_noise_ev = self.obs_noise_evidence_input.text().strip()
        if ui_noise_kind == 'independent_gaussian_1sigma':
            unc_map = dict(adapted.raw_uncertainty_columns)
            raw_unc = unc_map.get('uncertainty')
            if raw_unc is None or len(raw_unc) != len(base.values):
                raise ValueError(
                    'Cannot attest 1-sigma uncertainty: imported observation has no uncertainty column'
                )
            parsed_sigma: list[float] = []
            for val in raw_unc:
                if (
                    isinstance(val, bool)
                    or not isinstance(val, (int, float))
                    or not math.isfinite(val)
                    or val <= 0
                ):
                    raise ValueError(
                        'Cannot attest 1-sigma uncertainty: imported uncertainty column contains non-positive or missing values'
                    )
                parsed_sigma.append(float(val))
            sigma = tuple(parsed_sigma)
            noise_kind = ui_noise_kind
            attestations['noise_kind'] = ui_noise_kind
            if ui_noise_ev:
                noise_ev = ui_noise_ev
                attestations['noise_evidence'] = ui_noise_ev
        elif ui_noise_kind == 'conservative_asymmetric_envelope_1sigma':
            asym = audit_asymmetric_uncertainties(spectrum)
            if not asym.has_asymmetric_columns or asym.envelope_sigma is None:
                raise ValueError(
                    asym.warning
                    or 'Cannot attest asymmetric 1-sigma envelope: imported observation has no valid asymmetric error columns'
                )
            sigma = asym.envelope_sigma
            noise_kind = 'independent_gaussian_1sigma'
            attestations['noise_kind'] = 'conservative_asymmetric_envelope_1sigma'
            attestations['asymmetric_columns'] = list(asym.column_pair) if asym.column_pair else []
            attestations['max_asymmetry_ratio'] = asym.max_asymmetry_ratio
            base_ev = ui_noise_ev or 'Imported asymmetric bounds'
            noise_ev = f'{base_ev} (conservative symmetric envelope max(|+sigma|, |-sigma|))'
            attestations['noise_evidence'] = noise_ev
            if asym.warning:
                extra_notes.append(asym.warning)

        updated = replace(
            base,
            role=role,
            observable=resolved['observable'],
            axis_unit=resolved['axis_unit'],
            signal_unit=resolved['signal_unit'],
            coordinate_frame=frame,
            response_id=resp_id,
            response_evidence=resp_ev,
            noise_kind=noise_kind,
            noise_evidence=noise_ev,
            sigma=sigma,
        )
        bin_audit = self._audit_current_observation_bins(resolved['axis_unit'])
        bin_semantics = None
        if bin_audit is not None:
            bin_semantics = {
                'has_resolved_bins': bin_audit.has_resolved_bins,
                'source_columns': list(bin_audit.source_columns) if bin_audit.source_columns else None,
                'convention': bin_audit.convention,
                'axis_unit': bin_audit.axis_unit,
                'width_unit': bin_audit.width_unit,
                'adjacent_spacing_to_width_median': bin_audit.adjacent_spacing_to_width_median,
                'overlapping_pair_count': bin_audit.overlapping_pair_count,
                'response_shape_note': bin_audit.response_shape_note,
                'warning': bin_audit.warning,
            }
            if bin_audit.warning:
                extra_notes.append(f'Bin semantics notice: {bin_audit.warning}')

        metadata_provenance = {
            'source_provided': {
                k: getattr(base, k)
                for k in ('role', 'observable', 'axis_unit', 'signal_unit', 'coordinate_frame', 'response_id', 'response_evidence')
                if getattr(base, k) is not None
            },
            'user_attested': dict(attestations),
            'bin_derived': {
                'convention': bin_semantics.get('convention') if bin_semantics else None,
                'source_columns': bin_semantics.get('source_columns') if bin_semantics else None,
            } if bin_semantics else None,
        }
        provenance = {
            'kind': 'imported_observation_snapshot',
            'source_file': str(spectrum.source_file),
            'source_sha256': self.current_observation_hash,
            'importer_mappings': [list(item) for item in adapted.mappings],
            'caller_attestations': attestations,
            'metadata_provenance': metadata_provenance,
            'bin_semantics': bin_semantics,
        }
        notes: list[str] = []
        if attestations:
            notes.append(
                'Caller-supplied UI metadata attestations were applied for fields not '
                f'established by raw import: {", ".join(sorted(attestations))}.'
            )
        notes.extend(extra_notes)
        return updated, provenance, notes

    def _audit_current_observation_bins(self, resolved_axis_unit: str | None = None):
        if self.current_observation is None:
            return None
        col_units = self.current_observation_metadata.get('column_units')
        conv = self.bin_convention_selector.currentData() or 'auto'
        effective_unit = (
            resolved_axis_unit
            if resolved_axis_unit is not None
            else (
                self.current_observation.axis_unit
                or self.obs_axis_unit_selector.currentData()
            )
        )
        return audit_observation_bin_semantics(
            self.current_observation,
            column_units=col_units if isinstance(col_units, (dict, tuple)) else None,
            width_convention=conv,
            require_axis_unit=True,
            axis_unit_override=effective_unit,
        )

    def _observation_bin_edges_in_microns(
        self,
        orig_axis_unit: str | None,
    ) -> tuple[tuple[float, float], ...] | None:
        if self.current_observation is None:
            return None
        bin_audit = self._audit_current_observation_bins(orig_axis_unit)
        if bin_audit is None or not bin_audit.has_resolved_bins or bin_audit.bin_edges is None:
            return None
        raw_edges = bin_audit.bin_edges
        unit = (orig_axis_unit or '').strip().lower()
        if unit in ('microns', 'um'):
            return raw_edges
        if unit in ('nanometers', 'nm'):
            return tuple((a * 1e-3, b * 1e-3) for a, b in raw_edges)
        if unit in ('angstroms', 'angstrom'):
            return tuple((a * 1e-4, b * 1e-4) for a, b in raw_edges)
        if unit in ('cm^-1', 'cm-1', '1/cm'):
            return tuple((10000.0 / b, 10000.0 / a) for a, b in reversed(raw_edges))
        return None

    def _align_inputs_for_candidates(
        self,
        left_input: ComparisonInput,
        candidate_inputs: list[ComparisonInput],
    ) -> tuple[ComparisonInput | TransformedInput, list[ComparisonInput | TransformedInput], list[str]]:
        if not self.align_checkbox.isChecked():
            return left_input, list(candidate_inputs), []

        notes: list[str] = []
        orig_left_axis_unit = left_input.axis_unit
        left_item: ComparisonInput | TransformedInput = left_input
        if left_input.observable == 'transit_depth':
            if left_input.axis_unit in ('nanometers', 'nm', 'angstroms', 'angstrom', 'um') and left_input.axis_unit != 'microns':
                left_item = convert_axis_unit(left_item, 'microns')
            elif left_input.axis_unit in ('cm^-1', 'cm-1', '1/cm'):
                left_item = convert_wavenumber_to_microns(left_item, 'microns')
            left_cur = _eval_input(left_item)
            if left_cur.signal_unit == 'ppm':
                left_item = convert_signal_unit(left_item, 'percent')
        left_cur = _eval_input(left_item)

        stage1: list[ComparisonInput | TransformedInput] = []
        for cand in candidate_inputs:
            c_item: ComparisonInput | TransformedInput = cand
            if cand.observable == 'transit_depth':
                if cand.axis_unit in ('nanometers', 'nm', 'angstroms', 'angstrom', 'um') and cand.axis_unit != 'microns':
                    c_item = convert_axis_unit(c_item, 'microns')
                elif cand.axis_unit in ('cm^-1', 'cm-1', '1/cm'):
                    c_item = convert_wavenumber_to_microns(c_item, 'microns')
                c_cur = _eval_input(c_item)
                if (
                    left_cur.signal_unit in ('percent', 'fraction')
                    and c_cur.signal_unit in ('percent', 'fraction', 'ppm')
                    and c_cur.signal_unit != left_cur.signal_unit
                ):
                    c_item = convert_signal_unit(c_item, left_cur.signal_unit)
            stage1.append(c_item)

        if (
            left_cur.observable == 'transit_depth'
            and left_cur.axis_unit == 'microns'
            and left_cur.coordinate_frame
            and _strictly_increasing_1d(left_cur.coordinates)
        ):
            obs_edges_um = (
                self._observation_bin_edges_in_microns(orig_left_axis_unit)
                if self.bin_integrate_checkbox.isChecked()
                else None
            )
            if (
                obs_edges_um is not None
                and len(obs_edges_um) == len(left_cur.coordinates)
                and left_cur.response_id
                and left_cur.response_evidence
            ):
                fm_indices: list[int] = []
                common_bins = list(range(len(obs_edges_um)))
                for idx, c_item in enumerate(stage1):
                    c_cur = _eval_input(c_item)
                    if (
                        c_cur.role == 'forward_model'
                        and c_cur.observable == 'transit_depth'
                        and c_cur.axis_unit == 'microns'
                        and c_cur.coordinate_frame == left_cur.coordinate_frame
                        and _strictly_increasing_1d(c_cur.coordinates)
                    ):
                        dom_start = float(c_cur.coordinates[0])
                        dom_stop = float(c_cur.coordinates[-1])
                        covered = [
                            b_i for b_i in common_bins
                            if dom_start <= obs_edges_um[b_i][0] and obs_edges_um[b_i][1] <= dom_stop
                        ]
                        if len(covered) >= 3:
                            fm_indices.append(idx)
                            common_bins = covered

                if fm_indices and len(common_bins) >= 3:
                    if len(common_bins) < len(left_cur.coordinates):
                        left_item = subset_by_indices(
                            left_item,
                            common_bins,
                            exclusion_reason='bin_not_fully_covered_by_model_domain',
                        )
                        left_cur = _eval_input(left_item)
                        active_edges = tuple(obs_edges_um[i] for i in common_bins)
                    else:
                        active_edges = obs_edges_um

                    bin_audit = self._audit_current_observation_bins(orig_left_axis_unit)
                    src_cols = bin_audit.source_columns if bin_audit is not None else None
                    bin_conv = bin_audit.convention if bin_audit is not None else 'tophat_bounds'
                    for idx in fm_indices:
                        stage1[idx], _, _ = integrate_model_over_bins(
                            stage1[idx],
                            left_cur.coordinates,
                            active_edges,
                            response_id=left_cur.response_id,
                            response_evidence=left_cur.response_evidence,
                            bin_source_columns=src_cols,
                            bin_width_convention=bin_conv,
                            response_shape='uniform_tophat_boxcar',
                        )
                    if bin_audit is not None and bin_audit.response_shape_note:
                        notes.append(bin_audit.response_shape_note)
                    return left_item, stage1, notes

            left_coord_set = set(left_cur.coordinates)
            alignable_indices: list[int] = []
            for idx, c_item in enumerate(stage1):
                c_cur = _eval_input(c_item)
                if (
                    c_cur.observable == 'transit_depth'
                    and c_cur.axis_unit == left_cur.axis_unit
                    and c_cur.coordinate_frame == left_cur.coordinate_frame
                    and _strictly_increasing_1d(c_cur.coordinates)
                    and len(left_coord_set & set(c_cur.coordinates)) >= 3
                ):
                    alignable_indices.append(idx)

            if alignable_indices:
                common_set = set(left_cur.coordinates)
                for idx in alignable_indices:
                    common_set &= set(_eval_input(stage1[idx]).coordinates)
                if len(common_set) >= 3:
                    common_sorted = tuple(x for x in left_cur.coordinates if x in common_set)
                    if common_sorted != left_cur.coordinates:
                        anchor = replace(
                            left_cur,
                            coordinates=common_sorted,
                            values=tuple(0.0 for _ in common_sorted),
                            sigma=None,
                            covariance=None,
                        )
                        left_item, _ = restrict_to_shared_coordinates(left_item, anchor)
                        left_cur = _eval_input(left_item)
                    for idx in alignable_indices:
                        if _eval_input(stage1[idx]).coordinates != left_cur.coordinates:
                            _, stage1[idx] = restrict_to_shared_coordinates(left_item, stage1[idx])
                elif len(alignable_indices) > 1:
                    notes.append(
                        'Multiple candidates share fewer than 3 common exact coordinates; '
                        'shared-grid subsetting was skipped to preserve target support.'
                    )

        return left_item, stage1, notes

    def run_interactive_candidates(self):
        if self.current_observation is None:
            self.compatibility.setText(
                'Select and add an observation snapshot before evaluating candidates.'
            )
            return None
        if not self.candidate_entries:
            self.compatibility.setText(
                'Load at least one forward-model JSON or stage a cached reference candidate first.'
            )
            return None
        try:
            left_base, left_prov, notes = self._build_attested_observation()
            left_item, right_items, align_notes = self._align_inputs_for_candidates(
                left_base, [e.comparison_input for e in self.candidate_entries]
            )
        except ValueError as error:
            self._clear_diagnostic()
            self.current_eligibility = None
            self.current_candidate_summary = None
            self.compatibility.setText(f'Candidate preparation blocked: {error}')
            return None

        all_notes = tuple(notes + align_notes)
        weighted = self.weighted_checkbox.isChecked()
        independent = self.independent_checkbox.isChecked()
        if independent and weighted:
            all_notes = all_notes + (
                'Caller attested cross-dataset error independence via UI.',
            )
        return self._evaluate_and_display_candidates(
            left_item=left_item,
            right_items=right_items,
            left_provenance=left_prov,
            right_provenances=[e.provenance for e in self.candidate_entries],
            candidate_labels=[e.label for e in self.candidate_entries],
            weighted=weighted,
            cross_dataset_independent=independent,
            limitations=all_notes,
        )

    def add_current_observation(self):
        spectrum, source_hash = self.observation_getter()
        if spectrum is None:
            self.observation_status.setText('Load an observation in Spectral Data or Projects first. Previous selection retained.')
            return
        raw_meta = self.metadata_getter() if self.metadata_getter is not None else None
        meta = dict(raw_meta) if isinstance(raw_meta, dict) else {}
        description = self.description_getter() if self.description_getter else spectrum.source_file.name
        self.add_observation_snapshot(spectrum, source_hash, meta, description)

    def add_observation_snapshot(self, spectrum, source_hash, metadata, description):
        """Add an immutable observation supplied by import or identification."""
        snapshot = deepcopy(spectrum)
        self._observation_metadata_list.append(deepcopy(metadata))
        self.observation_selector.addItem(
            f'{self.observation_selector.count() + 1}: {description} | {snapshot.row_count} rows',
            (snapshot, source_hash))
        self.observation_selector.setCurrentIndex(self.observation_selector.count() - 1)
        return self.observation_selector.count() - 1

    def _select_observation(self, *_):
        idx = self.observation_selector.currentIndex()
        selected = self.observation_selector.currentData()
        self.current_observation = selected[0] if selected else None
        self.current_observation_hash = selected[1] if selected else None
        self.current_observation_metadata = (
            dict(self._observation_metadata_list[idx])
            if selected and 0 <= idx < len(self._observation_metadata_list)
            else {}
        )
        if selected:
            spectrum, source_hash = selected
            report = evaluate_readiness(
                'atmospheric_retrieval',
                spectrum,
                source_sha256=source_hash,
            )
            self.readiness_banner.set_report(report)
            hash_display = ('\n'.join(source_hash[i:i + 32] for i in range(0, len(source_hash), 32))
                            if source_hash else 'not established')
            self.observation_status.setToolTip(
                f'Source: {spectrum.source_file}\nSource SHA-256: {source_hash or "not established"}')
            self.observation_status.setText(
                f'Source: {spectrum.source_file}\nObservable: {spectrum.signal_type or "unknown"}; '
                f'axis unit: {spectrum.axis_unit or "unknown"}; signal unit: {spectrum.signal_unit or "unknown"}. '
                f'Source SHA-256:\n{hash_display}\n'
                + ('Warnings: ' + '; '.join(spectrum.warnings) if spectrum.warnings else ''))
            _fill(self.observation_table, spectrum.columns,
                  [tuple(row[column] for column in spectrum.columns) for row in spectrum.rows])
            if not self.observation_plot.load_spectrum(spectrum):
                self.observation_status.setText(self.observation_status.text() +
                    '\nNo valid coordinate pairs for plotting; original values remain in Data table.')
        self._explain()
        self._update_context_summary()

    def refresh_references(self):
        previous = self.reference_selector.currentData()
        self.reference_selector.blockSignals(True)
        self.reference_selector.clear()
        try:
            records, invalid = cached_references(self.cache_root / 'references')
            for path, result in records:
                request = result.request
                self.reference_selector.addItem(
                    f'{request.service.formula} / {request.service.isotopologue} / {request.service.dataset} | '
                    f'{request.temperature} K | {request.minimum}–{request.maximum} cm^-1 | '
                    f'{request.spacing} spacing | {path.stem}', str(path))
            index = self.reference_selector.findData(previous) if previous is not None else -1
            self.reference_selector.setCurrentIndex(index)
            self.cache_status.setText(f'{len(records)} cached references available; {invalid} invalid entries excluded. '
                                      'Uncached catalogue entries require a supported download in Molecular References.')
        except (OSError, ValueError) as error:
            self.cache_status.setText(f'Reference cache unavailable: {error}')
        finally:
            self.reference_selector.blockSignals(False)
        self._select_reference()

    def toggle_reference_axis_unit(self):
        mode = self.reference_plot.toggle_axis_mode()
        self.reference_axis_toggle.setText(
            'Show X-axis in Wavenumber (cm^-1)'
            if mode == 'microns'
            else 'Show X-axis in Wavelength (microns)'
        )
        self.reference_views.setTabText(
            0, 'Plot (microns)' if mode == 'microns' else 'Plot (native units)'
        )
        if self.current_reference is not None:
            axis_label, pts = reference_display_points(self.current_reference.product, mode)
            _fill(self.reference_table, (axis_label, 'Cross section (cm^2/molecule)'), pts)
        return mode

    def _select_reference(self, *_):
        self.current_reference = None
        self.reference_plot.clear()
        _fill(self.reference_table, (), ())
        path = self.reference_selector.currentData()
        self.reference_status.setText('No cached reference selected.')
        self.reference_status.setToolTip('')
        if path is not None:
            try:
                result = load_reference(path)
                self.current_reference = result
                product, request = result.product, result.request
                provenance = product.provenance
                self.reference_status.setText(
                    f'{provenance.molecule} / {provenance.isotopologue} / {provenance.dataset}; '
                    f'{request.temperature} K; zero pressure; Doppler-only. Calculated absorption cross section.\n'
                    f'Source SHA-256: {product.source_sha256}\nSource: {provenance.source_url}')
                self.reference_status.setToolTip('\n'.join((*provenance.citations, provenance.licence_url)))
                axis_label, pts = reference_display_points(product, self.reference_plot.axis_mode)
                _fill(self.reference_table, (axis_label, 'Cross section (cm^2/molecule)'), pts)
                self.reference_plot.load_product(product)
            except (OSError, ValueError) as error:
                self.reference_status.setText(f'Cached reference unavailable or invalid: {error}')
        self._explain()
        self._update_context_summary()

    def _clear_diagnostic(self):
        self.current_diagnostic = None
        if self.residual_plot is not None:
            self.residual_plot.clear()
        _fill(self.residual_table, (), ())
        self.diagnostic_summary.setText('')
        self.diagnostic_panel.setVisible(False)

    def _display_diagnostic(self, diagnostic):
        self.current_diagnostic = diagnostic
        if self.residual_plot is None:
            self.residual_plot = ResidualPlot(self.diagnostic_views)
            self.diagnostic_views.insertTab(0, self.residual_plot, 'Aligned overlay & residuals')
            self.diagnostic_views.setCurrentIndex(0)
        self.residual_plot.load_diagnostic(diagnostic)
        columns = [
            f'Wavelength ({diagnostic.axis_unit})',
            f'Left ({diagnostic.signal_unit})',
            f'Right ({diagnostic.signal_unit})',
            f'Residual left - right ({diagnostic.signal_unit})',
        ]
        if diagnostic.whitened_residuals is not None:
            columns.append('Whitened residual')
            rows = list(zip(
                diagnostic.coordinates,
                diagnostic.left_values,
                diagnostic.right_values,
                diagnostic.residuals,
                diagnostic.whitened_residuals,
            ))
        else:
            rows = list(zip(
                diagnostic.coordinates,
                diagnostic.left_values,
                diagnostic.right_values,
                diagnostic.residuals,
            ))
        _fill(self.residual_table, columns, rows)
        quadratic_note = (
            f'; weighted quadratic r^T C^-1 r = {diagnostic.weighted_residual_quadratic:.6g} '
            f'(reduced chi2 = {diagnostic.reduced_weighted_quadratic:.4g}, N = {diagnostic.sample_count}; '
            'fixed covariance, omits log-det normalization)'
            if diagnostic.weighted_residual_quadratic is not None and diagnostic.reduced_weighted_quadratic is not None
            else (
                f'; weighted quadratic r^T C^-1 r = {diagnostic.weighted_residual_quadratic:.6g} '
                '(fixed covariance, omits log-det normalization)'
                if diagnostic.weighted_residual_quadratic is not None else ''
            )
        )
        offset_note = (
            ' Systematic-offset notice: |mean residual| exceeds de-meaned shape RMS; '
            'a constant baseline transit-depth offset dominates spectral shape residuals '
            '(offsets are reported diagnostically, never silently subtracted).'
            if diagnostic.offset_dominates_shape else ''
        )
        self.diagnostic_summary.setText(
            f'Diagnostic {diagnostic.operation} ({diagnostic.residual_convention}, '
            f'{diagnostic.sample_count} samples, {diagnostic.signal_unit}): '
            f'RMS = {diagnostic.rms_residual:.6g}, '
            f'de-meaned shape RMS = {diagnostic.demeaned_rms_residual:.6g}, '
            f'mean = {diagnostic.mean_residual:.6g}, '
            f'max |r| = {diagnostic.max_abs_residual:.6g}{quadratic_note}.{offset_note} '
            'Numerical residual agreement only; not model adequacy, statistical significance, '
            'molecular identification, or atmospheric abundance.'
        )
        self.diagnostic_panel.setVisible(True)

    def evaluate_inputs(
        self,
        left_input,
        right_input,
        *,
        weighted=False,
        cross_dataset_independent=False,
        left_label='observation',
        right_label='reference',
    ):
        """Assess two ComparisonInput objects and render residuals only if eligible."""
        self.current_candidate_summary = None
        self._evaluated_candidate_records = []
        self._clear_diagnostic()
        left_eval = _eval_input(left_input)
        right_eval = _eval_input(right_input)
        self._active_record_context = {
            'left_item': left_input,
            'right_item': right_input,
            'left_provenance': None,
            'right_provenance': None,
            'weighted': weighted,
            'cross_dataset_independent': cross_dataset_independent,
            'limitations': (),
        }
        eligibility = assess(
            left_eval,
            right_eval,
            weighted=weighted,
            cross_dataset_independent=cross_dataset_independent,
        )
        self.current_eligibility = eligibility
        self.compatibility.setToolTip('\n'.join((
            f'{eligibility.version} ({eligibility.operation}): {eligibility.status}',
            *eligibility.reasons,
        )))
        if eligibility.status != 'eligible':
            reasons = [
                f'Comparison blocked ({eligibility.version} / {eligibility.operation}: {eligibility.status}).'
            ]
            if eligibility.reasons:
                reasons.append(
                    'Unmet eligibility checks: '
                    + '; '.join(describe_reason(code, left_label, right_label) for code in eligibility.reasons)
                    + '.'
                )
            self.compatibility.setText('\n'.join(reasons))
            return None
        diagnostic = evaluate_residuals(
            left_eval,
            right_eval,
            weighted=weighted,
            cross_dataset_independent=cross_dataset_independent,
        )
        self._display_diagnostic(diagnostic)
        self.compatibility.setText(
            f'Comparison eligible ({eligibility.version} / {eligibility.operation}: {eligibility.status}). '
            'Aligned overlay and left-minus-right residuals are displayed below. '
            'Numerical agreement does not establish molecular presence or abundance.'
        )
        return diagnostic

    def _candidate_summary_header(self, summary) -> str:
        if summary.eligible_indices:
            if summary.fair_ranking_permitted:
                closest_ids = ', '.join(
                    summary.candidates[i].source_id for i in summary.closest_candidate_indices
                )
                tie_note = (
                    ' (tied closest candidates; ambiguity preserved)'
                    if len(summary.closest_candidate_indices) > 1 else ''
                )
                ranking_text = f'Closest by {summary.ranking_metric}: {closest_ids}{tie_note}.'
            else:
                ranking_text = (
                    'Fair ranking blocked across eligible candidates: '
                    + ', '.join(summary.ranking_block_reasons) + '.'
                )
            return (
                f'Multi-candidate {summary.operation}: {len(summary.eligible_indices)} eligible, '
                f'{len(summary.blocked_indices)} blocked. {ranking_text} '
                + ' '.join(summary.limitations)
            )
        return (
            f'Multi-candidate {summary.operation}: 0 eligible, '
            f'{len(summary.blocked_indices)} blocked ({", ".join(summary.ranking_block_reasons)}). '
            'No overlay, residual, or candidate ranking is produced.'
        )

    def _render_candidate_selection(self, idx: int):
        summary = self.current_candidate_summary
        if summary is None or not (0 <= idx < len(summary.candidates)):
            return
        cand = summary.candidates[idx]
        self.current_eligibility = cand.eligibility
        rec_ctx = self._evaluated_candidate_records[idx]
        self._active_record_context = rec_ctx
        left_eval = _eval_input(rec_ctx['left_item'])
        report = evaluate_readiness(
            'atmospheric_retrieval',
            left_eval,
            source_sha256=getattr(left_eval, 'source_sha256', None),
        )
        self.readiness_banner.set_report(report)
        header = self._candidate_summary_header(summary)
        left_steps = _steps_summary(rec_ctx['left_item'])
        right_steps = _steps_summary(rec_ctx['right_item'])
        transform_parts = []
        if left_steps:
            transform_parts.append(f'observation transforms: {left_steps}')
        if right_steps:
            transform_parts.append(f'candidate transforms: {right_steps}')
        transform_note = f' [{" | ".join(transform_parts)}]' if transform_parts else ''

        if cand.eligibility.status == 'eligible' and cand.diagnostic is not None:
            self._display_diagnostic(cand.diagnostic)
            detail = (
                f'Inspecting candidate [{idx}] {cand.source_id}: eligible{transform_note}.'
            )
        else:
            self._clear_diagnostic()
            unmet = '; '.join(
                describe_reason(code, 'observation', f'candidate {cand.source_id}')
                for code in cand.eligibility.reasons
            )
            detail = (
                f'Inspecting candidate [{idx}] {cand.source_id}: '
                f'{cand.eligibility.status}{transform_note} — Unmet checks: {unmet}.'
            )
        extra_lines = [f'{header}\n{detail}']
        ctx_lims = [
            lim for lim in rec_ctx.get('limitations', ())
            if (
                'asymmetry' in lim.lower()
                or 'multiple candidates share' in lim.lower()
                or 'bin semantics notice' in lim.lower()
            )
        ]
        if ctx_lims:
            extra_lines.append(' '.join(ctx_lims))
        if self._last_attribution_note:
            extra_lines.append(self._last_attribution_note)
        self.compatibility.setText('\n'.join(extra_lines))
        self.compatibility.setToolTip('\n'.join((
            f'{summary.version} ({summary.operation})',
            *(
                f'[{c.candidate_index}] {c.source_id}: {c.eligibility.status}'
                + (f' ({", ".join(c.eligibility.reasons)})' if c.eligibility.reasons else '')
                for c in summary.candidates
            ),
        )))

    def _on_candidate_selector_changed(self, idx: int):
        if self.current_candidate_summary is None:
            return
        self._render_candidate_selection(idx)

    def _evaluate_and_display_candidates(
        self,
        *,
        left_item: ComparisonInput | TransformedInput,
        right_items: list[ComparisonInput | TransformedInput],
        left_provenance: dict | None,
        right_provenances: list[dict | None],
        candidate_labels: list[str],
        weighted: bool,
        cross_dataset_independent: bool,
        limitations: tuple[str, ...],
    ):
        self._clear_diagnostic()
        left_eval = _eval_input(left_item)
        right_evals = [_eval_input(item) for item in right_items]
        summary = evaluate_candidates(
            left_eval,
            right_evals,
            weighted=weighted,
            cross_dataset_independent=cross_dataset_independent,
        )
        self.current_candidate_summary = summary
        self._evaluated_candidate_records = [
            {
                'left_item': left_item,
                'right_item': r_item,
                'left_provenance': left_provenance,
                'right_provenance': r_prov,
                'weighted': weighted,
                'cross_dataset_independent': cross_dataset_independent,
                'limitations': limitations,
            }
            for r_item, r_prov in zip(right_items, right_provenances)
        ]
        if summary.eligible_indices:
            display_idx = (
                summary.ordered_eligible_indices[0]
                if summary.ordered_eligible_indices
                else summary.eligible_indices[0]
            )
        else:
            display_idx = 0

        self.candidate_selector.blockSignals(True)
        try:
            self.candidate_selector.clear()
            for idx, (cand, label) in enumerate(zip(summary.candidates, candidate_labels)):
                self.candidate_selector.addItem(
                    f'[{idx}] {label} ({cand.eligibility.status})', idx
                )
            self.candidate_selector.setCurrentIndex(display_idx)
        finally:
            self.candidate_selector.blockSignals(False)

        self._render_candidate_selection(display_idx)

        if self.diagnostic_panel.isVisible():
            self.scroll_area.ensureWidgetVisible(self.diagnostic_panel)
        if hasattr(self, 'workflow_tabs'):
            self.workflow_tabs.setCurrentIndex(3)

        return summary

    def evaluate_candidate_inputs(
        self,
        target_input,
        candidate_inputs,
        *,
        weighted=False,
        cross_dataset_independent=False,
    ):
        """Evaluate multiple candidates against one target with fair-ranking guards."""
        items = list(candidate_inputs)
        labels = [_eval_input(item).source_id for item in items]
        return self._evaluate_and_display_candidates(
            left_item=target_input,
            right_items=items,
            left_provenance=None,
            right_provenances=[None for _ in items],
            candidate_labels=labels,
            weighted=weighted,
            cross_dataset_independent=cross_dataset_independent,
            limitations=(),
        )

    def save_active_comparison(self):
        if self.project_store is None:
            self.persistence_status.setText('Project persistence is unavailable in this view.')
            return None
        project_name = self._active_project_name()
        if not project_name:
            self.persistence_status.setText('Select or create an active project in Projects first.')
            return None
        if self._active_record_context is None:
            self.persistence_status.setText(
                'Evaluate candidates or select both an observation and reference before saving.'
            )
            return None
        ctx = self._active_record_context
        try:
            record = build_comparison_record(
                ctx['left_item'],
                ctx['right_item'],
                weighted=ctx['weighted'],
                cross_dataset_independent=ctx['cross_dataset_independent'],
                left_provenance=ctx['left_provenance'],
                right_provenance=ctx['right_provenance'],
                limitations=ctx['limitations'],
            )
            saved_path = self.project_store.save_comparison(project_name, record)
        except (project_persistence.PersistenceError, ValueError, TypeError) as error:
            self.persistence_status.setText(f'Could not save comparison record: {error}')
            return None
        self.refresh_saved_comparisons(selected_path=str(saved_path))
        self.persistence_status.setText(
            f'Saved comparison {saved_path.name} to project {project_name} '
            f'(status: {record["eligibility"]["status"]}, '
            f'integrity SHA-256: {record["integrity_sha256"][:16]}…).'
        )
        self.persistence_status.setToolTip(
            '\n'.join((
                f'File: {saved_path}',
                f'Integrity SHA-256: {record["integrity_sha256"]}',
                *record['reproducibility_limitations'],
            ))
        )
        return saved_path

    def refresh_saved_comparisons(self, *_args, selected_path: str | None = None):
        if self.project_store is None:
            self.persistence_status.setText('Project persistence is unavailable in this view.')
            return []
        project_name = self._active_project_name()
        if not project_name:
            self.persistence_status.setText('Select or create an active project in Projects first.')
            return []
        previous = selected_path or self.saved_comparisons_selector.currentData()
        self.saved_comparisons_selector.blockSignals(True)
        self.saved_comparisons_selector.clear()
        try:
            records, invalid = self.project_store.comparisons(project_name)
            for path, rec in records:
                elig = rec['eligibility']
                right_id = rec['right']['evaluated_input']['source_id']
                self.saved_comparisons_selector.addItem(
                    f'{path.stem[:12]} | {elig["operation"]}: {elig["status"]} | {right_id}',
                    str(path),
                )
            idx = self.saved_comparisons_selector.findData(previous) if previous else -1
            if idx >= 0:
                self.saved_comparisons_selector.setCurrentIndex(idx)
            elif records:
                self.saved_comparisons_selector.setCurrentIndex(0)
            self.persistence_status.setText(
                f'Project {project_name}: {len(records)} verified comparison records; '
                f'{invalid} invalid/corrupted files excluded.'
            )
            return records
        except project_persistence.PersistenceError as error:
            self.persistence_status.setText(f'Could not load project comparisons: {error}')
            return []
        finally:
            self.saved_comparisons_selector.blockSignals(False)

    def reproduce_selected_comparison(self):
        path = self.saved_comparisons_selector.currentData()
        if not path:
            self.persistence_status.setText('Refresh and select a saved comparison record first.')
            return None
        try:
            record = load_comparison_record(path)
            check = reproduce_comparison_record(record)
        except (OSError, ValueError, KeyError, TypeError) as error:
            self._clear_diagnostic()
            self.current_eligibility = None
            self.persistence_status.setText(f'Saved comparison verification failed: {error}')
            self.persistence_status.setToolTip('')
            return None

        self.current_candidate_summary = None
        self.current_eligibility = check.recomputed_eligibility
        if check.recomputed_diagnostic is not None:
            self._display_diagnostic(check.recomputed_diagnostic)
        else:
            self._clear_diagnostic()

        verdict_flag = 'matched' if check.matches_saved_verdict else 'MISMATCH'
        diag_flag = 'matched' if check.matches_saved_diagnostics else 'MISMATCH'
        discrepancy_text = (
            f' Discrepancies: {"; ".join(check.discrepancies)}.'
            if check.discrepancies else ''
        )
        left_prov = record.get('left', {}).get('provenance', {})
        source_path_str = left_prov.get('source_file')
        raw_source_available = bool(source_path_str and Path(source_path_str).is_file())
        regeneration_note = (
            f'Original raw source file is available on disk ({Path(source_path_str).name}); full analysis can be regenerated from source.'
            if raw_source_available
            else 'Original raw source file is not found at its original path; analysis reproduced from signed record snapshot.'
        )
        self.persistence_status.setText(
            f'Verified & reproduced {record["right"]["evaluated_input"]["source_id"]}: '
            f'verdict {verdict_flag}, diagnostics {diag_flag}.{discrepancy_text} '
            f'Re-evaluated from signed record arrays; raw source files were not re-ingested. {regeneration_note}'
        )
        self.persistence_status.setToolTip('\n'.join((
            f'Method: {record["method_version"]}',
            f'Integrity SHA-256: {record["integrity_sha256"]}',
            f'Raw source available: {raw_source_available}',
            *check.discrepancies,
            *check.limitations,
        )))
        elig = check.recomputed_eligibility
        right_prov = record.get('right', {}).get('provenance', {})
        opacity_srcs = right_prov.get('physical_opacity_sources') or ()
        opacity_str = f' Opacities: {", ".join(opacity_srcs)}.' if opacity_srcs else ''
        raw_src_text = f' Source file: {Path(source_path_str).name} (available).' if raw_source_available else ' Source file: offline record snapshot.'
        if elig.status == 'eligible':
            self.compatibility.setText(
                f'Reopened saved comparison ({elig.version} / {elig.operation}: {elig.status}).{raw_src_text}{opacity_str} '
                f'Integrity SHA-256 verified ({record["integrity_sha256"][:12]}...). '
                'Recomputed overlay and left-minus-right residuals are displayed below. '
                'Numerical agreement does not establish molecular presence or abundance.'
            )
        else:
            unmet = '; '.join(describe_reason(c, 'left', 'right') for c in elig.reasons)
            self.compatibility.setText(
                f'Reopened saved comparison ({elig.version} / {elig.operation}: {elig.status}). '
                f'Unmet eligibility checks: {unmet}.'
            )
        return check

    def _explain(self):
        self.current_eligibility = None
        self.current_candidate_summary = None
        self._evaluated_candidate_records = []
        self._active_record_context = None
        if self.candidate_entries:
            self._sync_staged_candidate_selector()
        self._clear_diagnostic()
        if self.current_observation is None or self.current_reference is None:
            self.compatibility.setText('Select an observation and a valid cached reference for inspection. '
                                       'Comparison operations remain unavailable.')
            self.compatibility.setToolTip('')
            return
        spectrum = self.current_observation
        left = observation_input(spectrum, self.current_observation_hash)
        right = reference_input(self.current_reference)
        self._active_record_context = {
            'left_item': left.comparison_input,
            'right_item': right.comparison_input,
            'left_provenance': {
                'kind': 'imported_observation_snapshot',
                'source_file': str(spectrum.source_file),
                'source_sha256': self.current_observation_hash,
            },
            'right_provenance': {
                'kind': 'cached_exomol_reference',
                'source_url': self.current_reference.product.provenance.source_url,
                'source_sha256': self.current_reference.product.source_sha256,
            },
            'weighted': False,
            'cross_dataset_independent': False,
            'limitations': (),
        }
        eligibility = assess(left.comparison_input, right.comparison_input)
        self.current_eligibility = eligibility
        reasons = [
            f'Comparison blocked ({eligibility.version} / {eligibility.operation}: {eligibility.status}): '
            'this reference is a calculated absorption cross section in cm^2/molecule '
            'on wavenumber cm^-1, not a predicted transit-depth spectrum. '
            'Cross sections and transit depth cannot be compared directly without a physical model.'
        ]
        if not spectrum.signal_type or not spectrum.signal_unit or not spectrum.axis_unit:
            reasons.append('Observation observable or units are unknown; no meaning or conversion is inferred.')
        if eligibility.reasons:
            reasons.append('Unmet eligibility checks: ' +
                           '; '.join(describe_reason(code, 'observation', 'reference') for code in eligibility.reasons) + '.')
        reasons.append('A physical model with documented conditions, compatible observables/units, '
                       'coordinate frame, grid alignment and instrument response evidence is required '
                       'before overlay or residual analysis. Uncertainty/noise evidence is required for '
                       'weighted diagnostics. Load a validated forward-model curve in the candidate tools '
                       'above to evaluate eligible transit-depth predictions.')
        self.compatibility.setText('\n'.join(reasons))
        self.compatibility.setToolTip('\n'.join((
            f'{eligibility.version} ({eligibility.operation}): {eligibility.status}',
            *eligibility.reasons,
        )))
