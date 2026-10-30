"""End-to-end UI integration tests for the six scientific workflow capabilities."""
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication

from ecas.ui.main_window import ECASWindow

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def app():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def window(tmp_path, app):
    widget = ECASWindow(projects_dir=tmp_path / "projects", reference_cache_dir=tmp_path / "cache")
    yield widget
    widget.close()


class TestWorkflowUIIntegration:
    def test_readiness_banner_in_ui(self, window, tmp_path):
        browser = window.comparison_browser
        id_panel = browser.identification_panel

        assert browser.readiness_banner is not None
        if id_panel is not None:
            assert id_panel.readiness_banner is not None

        # Import observation into main window
        feinstein_path = ROOT / "data/NASA/2026-10-27/feinstein-2023.tbl"
        if feinstein_path.exists():
            window._import_csv_from_path(str(feinstein_path))
            browser.add_current_observation()

            # Verify readiness banner in Comparison Browser
            assert not browser.readiness_banner.isHidden()
            assert "Ready" in browser.readiness_banner.summary_label.text() or "Blocked" in browser.readiness_banner.summary_label.text()

    def test_parameter_sensitivity_dialog(self, window, tmp_path):
        browser = window.comparison_browser
        feinstein_path = ROOT / "data/NASA/2026-10-27/feinstein-2023.tbl"
        if not feinstein_path.exists():
            pytest.skip("feinstein-2023.tbl not available")

        window._import_csv_from_path(str(feinstein_path))
        browser.add_current_observation()

        dlg = browser.open_parameter_sensitivity(exec_dialog=False)
        assert dlg is not None
        assert dlg.pert_selector.count() > 0
        assert dlg.degen_table.rowCount() > 0
        assert dlg.top_plot is not None
        assert dlg.bot_plot is not None

        # Test user interaction: switch parameter
        dlg.pert_selector.setCurrentIndex(1)
        assert dlg._current_pert_index == 1
        dlg.accept()

    def test_observation_consistency_dialog(self, window, tmp_path):
        browser = window.comparison_browser
        feinstein_path = ROOT / "data/NASA/2026-10-27/feinstein-2023.tbl"
        if not feinstein_path.exists():
            pytest.skip("feinstein-2023.tbl not available")

        # Add two observations
        window._import_csv_from_path(str(feinstein_path))
        browser.add_current_observation()
        # Add a second copy to test comparison
        browser.add_observation_snapshot(window.current_spectrum, "b" * 64, {}, "Reduction Copy")

        assert browser.observation_selector.count() >= 2
        dlg = browser.open_observation_consistency(exec_dialog=False)
        assert dlg is not None
        assert dlg.datasets_table.rowCount() >= 2
        assert dlg.pair_selector.count() >= 1

        # Check diagnostics populated
        assert len(dlg.metrics_label.text()) > 0
        dlg.accept()

    def test_assumptions_comparison_dialog(self, window):
        browser = window.comparison_browser
        dlg = browser.open_assumptions_comparison(exec_dialog=False)
        assert dlg is not None
        assert dlg.inv_table.rowCount() >= 2
        assert len(dlg.diffs_label.text()) > 0
        assert len(dlg.stats_label.text()) > 0

        # Test user interaction: switch variant selection
        dlg.sel_b.setCurrentIndex(0)
        dlg.accept()

    def test_fit_diagnostics_dialog(self, window):
        browser = window.comparison_browser
        dlg = browser.open_fit_diagnostics(exec_dialog=False)
        assert dlg is not None
        assert len(dlg.diag.plain_language_summary) > 0
        assert len(dlg.diag.progressive_disclosure_math) >= 4
        dlg.accept()

    def test_job_manager_dialog(self, window):
        browser = window.comparison_browser
        dlg = browser.open_job_manager(exec_dialog=False)
        assert dlg is not None
        assert dlg.jobs_table.rowCount() >= 1
        assert "# ECAS Scientific Analysis Report" in dlg.report_preview.toPlainText()
        dlg.accept()
