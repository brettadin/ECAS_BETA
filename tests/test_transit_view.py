"""Scientific validation and UI tests for the Transit & Orbit Visualizer."""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ecas.ui.main_window import ECASWindow
from ecas.ui.transit_view import (
    TransitVisualizerPage,
    compute_geometric_transit_flux,
    teff_to_hex,
)


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


class TestTransitPhysics:
    """Scientific validation of analytic geometric transit flux calculations."""

    def test_out_of_transit_flux_is_unity(self):
        k = 0.1
        b = 0.2
        # Planet is well outside stellar disk (|x| > 1 + k)
        x_out = np.array([-2.0, -1.5, 1.5, 2.0])
        flux = compute_geometric_transit_flux(x_out, b=b, k=k, u1=0.4)
        np.testing.assert_allclose(flux, 1.0, atol=1e-12)

    def test_center_of_transit_uniform_disk(self):
        k = 0.1
        b = 0.0
        x_center = np.array([0.0])
        # With u1 = 0 (uniform disk), central flux drop is exactly k^2
        flux = compute_geometric_transit_flux(x_center, b=b, k=k, u1=0.0)
        expected_drop = k**2
        np.testing.assert_allclose(flux[0], 1.0 - expected_drop, atol=1e-12)

    def test_limb_darkening_intensifies_central_transit(self):
        k = 0.1
        b = 0.0
        x_center = np.array([0.0])
        u1 = 0.4
        flux_uniform = compute_geometric_transit_flux(x_center, b=b, k=k, u1=0.0)
        flux_limb_darkened = compute_geometric_transit_flux(x_center, b=b, k=k, u1=u1)

        # Center of limb-darkened star is brighter than disk average, so occulting center drops more flux
        assert flux_limb_darkened[0] < flux_uniform[0]

        # Analytical ratio at center d=0: (1 - u1*(1-1)) / (1 - u1/3) = 1 / (1 - u1/3)
        expected_ld_factor = 1.0 / (1.0 - u1 / 3.0)
        expected_drop = (k**2) * expected_ld_factor
        np.testing.assert_allclose(1.0 - flux_limb_darkened[0], expected_drop, rtol=1e-6)

    def test_transit_light_curve_is_symmetric_and_monotonic_during_ingress(self):
        k = 0.08
        b = 0.3
        x_ingress = np.linspace(-1.5, 0.0, 100)
        flux_ingress = compute_geometric_transit_flux(x_ingress, b=b, k=k, u1=0.3)

        # Flux should be monotonically non-increasing as planet moves from outside to center
        diffs = np.diff(flux_ingress)
        assert np.all(diffs <= 1e-12)

        # Symmetry: F(-x) == F(x)
        x_egress = -x_ingress[::-1]
        flux_egress = compute_geometric_transit_flux(x_egress, b=b, k=k, u1=0.3)
        np.testing.assert_allclose(flux_ingress, flux_egress[::-1], atol=1e-12)

    def test_teff_to_hex_temperature_color_scale(self):
        cool_hex = teff_to_hex(3000.0)
        solar_hex = teff_to_hex(5778.0)
        hot_hex = teff_to_hex(12000.0)

        assert cool_hex.startswith("#")
        assert len(cool_hex) == 7
        # Cool star should have strong red component
        assert int(cool_hex[1:3], 16) >= 250
        # Hot star should have high blue component
        assert int(hot_hex[5:7], 16) >= 250


class TestTransitVisualizerUI:
    """UI interactions and integration with ECAS window and Comparisons workspace."""

    def test_page_components_and_preset_switching(self, app):
        page = TransitVisualizerPage()
        assert page.sky_view is not None
        assert page.light_curve is not None
        assert page.metrics_label is not None

        # Verify default preset WASP-39 b is loaded
        assert page.preset_combo.currentData() == "wasp-39b"
        assert "WASP-39 b" in page.preset_combo.currentText()
        assert pytest.approx(page.rpl_spin.value(), rel=1e-2) == 1.27

        # Switch preset to HD 209458 b
        idx_hd = page.preset_combo.findData("hd-209458b")
        assert idx_hd >= 0
        page.preset_combo.setCurrentIndex(idx_hd)
        assert pytest.approx(page.rpl_spin.value(), rel=1e-2) == 1.36
        assert "Geometric Depth" in page.metrics_label.text()

        page.close()

    def test_scrubber_slider_and_playback_toggle(self, app):
        page = TransitVisualizerPage()

        # Scrub slider to center (0.0)
        page.phase_slider.setValue(0)
        assert page._current_x == 0.0
        assert "Current Drop" in page.metrics_label.text()

        # Play / pause toggle
        assert not page._is_playing
        page.play_button.click()
        assert page._is_playing
        assert page._timer.isActive()
        assert "Pause" in page.play_button.text()

        # Advance tick
        cur_before = page._current_x
        page._on_tick()
        assert page._current_x > cur_before

        page.play_button.click()
        assert not page._is_playing
        assert not page._timer.isActive()
        assert "Play" in page.play_button.text()

        page.close()

    def test_open_in_comparisons_workspace_integration(self, app, tmp_path):
        window = ECASWindow(
            projects_dir=tmp_path / "projects",
            reference_cache_dir=tmp_path / "cache",
        )
        try:
            # Switch to Transit Visualizer page (index 7)
            window.navigation.setCurrentRow(7)
            assert window.pages.currentIndex() == 7
            transit_page = window.transit_page

            # Select HD 209458 b preset
            idx_hd = transit_page.preset_combo.findData("hd-209458b")
            transit_page.preset_combo.setCurrentIndex(idx_hd)

            # Click Apply to Comparisons button
            transit_page.apply_button.click()

            # Verify application switched to Comparisons page (index 4)
            assert window.navigation.currentRow() == 4
            assert window.pages.currentIndex() == 4

            # Verify the comparison browser planetary preset was updated
            assert window.comparison_browser.gen_preset_selector.currentData() == "hd-209458b"
        finally:
            window.close()
