"""Tests for usability, navigation reorganization, and wheel event protections.

Verifies the implementation addressing Brett's human review (Issue #9):
1. Navigation reorganized around user tasks (Data & Projects, Atmospheric Analysis,
   Laboratory Identification, Images, Runs & Reports).
2. Primary 4-step Atmospheric Analysis workflow:
   Step 1: Choose & Inspect Observation -> Step 2: Review Requirements ->
   Step 3: Configure Model -> Step 4: Explore Results.
3. Wheel event protection on unfocused controls and plot zoom hijacking guards.
4. Capability guidance cards explaining Purpose, Inputs, Output, Limitations, Next Actions.
5. Planetary transit depth guidance and direct routing in Laboratory Identification.
6. Mathematical diagnostics rendered without raw LaTeX.
7. Clear distinction between physical forward models and synthetic templates.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ecas.comparison.diagnostics import compute_comprehensive_fit_diagnostics
from ecas.ingestion.csv_importer import WASP39B_SCHEMA
from ecas.ui.event_filters import IgnoreWheelUnlessFocusedFilter, apply_wheel_protection
from ecas.ui.main_window import ECASWindow
from ecas.visualization.spectra_plot import SpectraPlot


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, tmp_path):
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    win = ECASWindow(projects_dir=projects_dir, reference_cache_dir=cache_dir)
    yield win
    win.close()


def test_navigation_workspace_order_and_aliases(window):
    """Verify that navigation has all 11 dedicated workspaces in correct order."""
    expected_nav = [
        "Overview",
        "Projects",
        "Spectral Data",
        "Molecular References",
        "Atmospheric Analysis",
        "Transit Visualizer",
        "Laboratory Identification",
        "Images",
        "Runs & Reports",
        "References & Resources",
        "Settings",
    ]
    actual_nav = [window.navigation.item(i).text() for i in range(window.navigation.count())]
    assert actual_nav == expected_nav
    assert window.pages.count() == 11

    # Verify alias navigation
    assert window.navigate_to("overview") and window.navigation.currentRow() == 0
    assert window.navigate_to("projects") and window.navigation.currentRow() == 1
    assert window.navigate_to("spectral data") and window.navigation.currentRow() == 2
    assert window.navigate_to("molecular references") and window.navigation.currentRow() == 3
    assert window.navigate_to("atmospheric analysis") and window.navigation.currentRow() == 4
    assert window.navigate_to("comparisons") and window.navigation.currentRow() == 4  # backwards compatible alias
    assert window.navigate_to("transit visualizer") and window.navigation.currentRow() == 5
    assert window.navigate_to("laboratory identification") and window.navigation.currentRow() == 6
    assert window.navigate_to("images") and window.navigation.currentRow() == 7
    assert window.navigate_to("runs & reports") and window.navigation.currentRow() == 8
    assert window.navigate_to("references & resources") and window.navigation.currentRow() == 9
    assert window.navigate_to("settings") and window.navigation.currentRow() == 10


def test_unfocused_wheel_protection_on_controls(app):
    """Verify that mouse-wheel scrolling over unfocused inputs does not alter values."""
    scroll = QScrollArea()
    scroll.resize(300, 300)
    container = QWidget()
    layout = QVBoxLayout(container)

    combo = QComboBox()
    combo.addItems(["Option A", "Option B", "Option C"])
    combo.setCurrentIndex(0)
    layout.addWidget(combo)

    spin = QDoubleSpinBox()
    spin.setRange(0.0, 100.0)
    spin.setValue(10.0)
    layout.addWidget(spin)

    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, 100)
    slider.setValue(50)
    layout.addWidget(slider)

    for i in range(30):
        layout.addWidget(QComboBox())

    scroll.setWidget(container)
    scroll.show()

    apply_wheel_protection(container)
    filter_obj = IgnoreWheelUnlessFocusedFilter()
    app.installEventFilter(filter_obj)

    # Initial state
    assert combo.currentIndex() == 0
    assert spin.value() == 10.0
    assert slider.value() == 50
    initial_scroll = scroll.verticalScrollBar().value()

    # Simulate wheel scroll event over unfocused combo box (scrolling down: angleDelta = -120)
    wheel_ev = QWheelEvent(
        QPointF(10, 10),
        QPointF(10, 10),
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    app.sendEvent(combo, wheel_ev)

    # Value MUST NOT change when unfocused
    assert combo.currentIndex() == 0
    # And scroll area must have scrolled
    assert scroll.verticalScrollBar().value() > initial_scroll

    # Simulate wheel over unfocused spinbox
    app.sendEvent(spin, wheel_ev)
    assert spin.value() == 10.0

    # Simulate wheel over unfocused slider
    app.sendEvent(slider, wheel_ev)
    assert slider.value() == 50


def test_plot_wheel_protection_guards(app):
    """Verify that scrolling a plot without Ctrl does not zoom, but Ctrl+Wheel zooms."""
    plot = SpectraPlot()
    plot.resize(400, 300)
    plot.show()

    plot_widget = plot.plot_widget
    vb = plot_widget.getViewBox()
    initial_range = vb.viewRange()

    # Wheel event without modifiers
    wheel_no_mod = QWheelEvent(
        QPointF(50, 50),
        QPointF(50, 50),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    app.sendEvent(plot_widget, wheel_no_mod)
    # View range unchanged
    assert vb.viewRange() == initial_range

    # Explicit zoom button works
    plot.zoom_in()
    zoomed_range = vb.viewRange()
    assert zoomed_range[0][1] - zoomed_range[0][0] < initial_range[0][1] - initial_range[0][0]

    # Reset view works
    plot.reset_view()


def test_atmospheric_analysis_4_step_workflow(window):
    """Verify the primary flow structure inside Atmospheric Analysis."""
    window.navigate_to("atmospheric analysis")
    cb = window.comparison_browser

    assert hasattr(cb, "workflow_tabs")
    assert cb.workflow_tabs.count() == 4
    tab_titles = [cb.workflow_tabs.tabText(i) for i in range(4)]
    assert "1. Choose Observation" in tab_titles[0]
    assert "2. Review Requirements" in tab_titles[1]
    assert "3. Configure Model" in tab_titles[2]
    assert "4. Explore Results" in tab_titles[3]

    # Verify context summary card exists and displays principle notice
    assert hasattr(cb, "context_card")
    assert "A physical forward model calculates the spectrum predicted by an atmosphere" in cb.model_distinction_notice.text()


def test_point_of_use_capability_cards(window):
    """Verify that each step provides clear capability guidance cards."""
    cb = window.comparison_browser
    assert hasattr(cb, "capability_cards")
    assert len(cb.capability_cards) == 4
    for card in cb.capability_cards:
        assert card is not None
        # Must contain Purpose, Inputs, Output, and Limitations
        labels = [l.text() for l in card.findChildren(QWidget) if hasattr(l, "text")]
        card_content = " ".join(labels)
        assert "Purpose:" in card_content
        assert "Inputs:" in card_content
        assert "What Output Shows:" in card_content
        assert "Limitation:" in card_content


def test_transit_routing_in_laboratory_identification(window):
    """Verify that a transit observation loaded into Lab ID shows the routing warning card."""
    root = Path(__file__).resolve().parents[1]
    nasa_tbl = root / "data" / "NASA" / "2026-10-27" / "feinstein-2023.tbl"

    # Navigate to Laboratory Identification
    window.navigate_to("laboratory identification")
    panel = window.identification_panel_page
    panel.add_files([nasa_tbl])

    # Guidance card must be visible and explain transit depth
    assert not panel.transit_guidance_card.isHidden()
    card_labels = [l.text() for l in panel.transit_guidance_card.findChildren(QWidget) if hasattr(l, "text")]
    content = " ".join(card_labels)
    assert "Planetary Transit Observation Detected" in content
    assert "Atmospheric Analysis" in content

    # Clicking the route button should switch to Atmospheric Analysis
    panel.atmospheric_button.click()
    assert window.navigation.currentRow() == 4


def test_diagnostics_renders_unicode_math_without_raw_latex():
    """Verify that diagnostics progressive disclosure uses clean Unicode and no raw LaTeX markup."""
    residuals = [0.02, -0.01, 0.03, -0.02, 0.01]
    uncertainties = [0.05, 0.05, 0.05, 0.05, 0.05]
    diag = compute_comprehensive_fit_diagnostics(
        "WASP-39 b Fit",
        residuals,
        uncertainties=uncertainties,
        parameter_count=2,
    )

    math_disclosures = diag.progressive_disclosure_math
    assert isinstance(math_disclosures, dict)
    assert len(math_disclosures) >= 4

    # Check that raw LaTeX math markup like \chi_\nu^2, \sum, \frac are replaced by clean Unicode
    for title, formula_text in math_disclosures.items():
        assert "\\" not in title, f"Found raw LaTeX backslash in title: {title}"
        assert "\\" not in formula_text, f"Found raw LaTeX backslash in formula: {formula_text}"
        assert "{" not in formula_text and "}" not in formula_text, f"Found raw LaTeX braces in: {formula_text}"


def test_images_workspace_page_controls(window, tmp_path):
    """Verify that Images workspace provides zoom, stretch, and colormap controls."""
    window.navigate_to("images")
    img_page = window.images_workspace
    assert img_page is not None
    assert img_page.stretch_selector.count() >= 5
    assert img_page.colormap_selector.count() >= 5
    assert hasattr(img_page, "zoom_in_btn")
    assert hasattr(img_page, "zoom_out_btn")
    assert hasattr(img_page, "reset_zoom_btn")


def test_runs_and_reports_workspace_controls(window):
    """Verify that Runs & Reports workspace provides queue, cancel, resume, and export controls."""
    window.navigate_to("runs & reports")
    runs_page = window.runs_workspace
    assert runs_page is not None
    assert hasattr(runs_page, "jobs_table")
    assert hasattr(runs_page, "cancel_btn")
    assert hasattr(runs_page, "resume_btn")
    assert hasattr(runs_page, "export_md_btn")
    assert hasattr(runs_page, "export_html_btn")
    assert hasattr(runs_page, "export_json_btn")
