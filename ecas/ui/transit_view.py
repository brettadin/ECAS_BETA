"""Educational and exploratory exoplanet transit visualizer.

Provides an interactive observer-frame sky view and synchronized geometric transit
light curve, demonstrating how star-planet relative scale (R_p / R_star)^2,
impact parameter b = (a cos i) / R_star, and limb darkening create the transit chord.

Scientific boundary:
This is an educational geometric simulator. In transmission spectroscopy, minute
atmospheric absorption features ΔD(λ) ~ 2 H R_p / R_star^2 (typically 100-500 ppm)
are superimposed upon this geometric baseline obscuration.
"""

from __future__ import annotations

import math
from typing import Callable, Optional

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ecas.comparison.model_generator import PLANET_PRESETS, PlanetAtmospherePreset, get_planet_preset

PLANET_ACCENT = "#4fc3f7"
BACKGROUND_COLOR = "#181b21"
BORDER_COLOR = "#2e3440"
TEXT_COLOR = "#d8dee9"
MUTED_TEXT = "#9aa7b8"


def teff_to_hex(teff_k: float) -> str:
    """Approximate blackbody color of a star using Tanner Helland's algorithm."""
    t = float(np.clip(teff_k, 1000.0, 40000.0)) / 100.0
    if t <= 66.0:
        r = 255.0
        g = 99.4708025861 * np.log(t) - 161.1195681661
        b = 0.0 if t <= 19.0 else 138.5177312231 * np.log(t - 10.0) - 305.0447927307
    else:
        r = 329.698727446 * (t - 60.0) ** -0.1332047592
        g = 288.1221695283 * (t - 60.0) ** -0.0755148492
        b = 255.0
    r, g, b = (int(np.clip(v, 0, 255)) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def compute_geometric_transit_flux(
    x_positions: np.ndarray,
    b: float,
    k: float,
    u1: float = 0.4,
) -> np.ndarray:
    """Compute analytic geometric transit light curve for a circular star and planet with linear limb-darkening."""
    d = np.sqrt(x_positions**2 + b**2)
    flux = np.ones_like(d, dtype=float)

    r1, r2 = 1.0, float(k)

    # 1. Fully inside the stellar disc: d <= 1 - k
    inside = d <= (r1 - r2)
    # Linear limb darkening approximation: I(r) = 1 - u1 * (1 - sqrt(1 - r^2))
    # Near center, flux drop is approximately k^2 * (1 - u1 * (1 - sqrt(1 - d^2))) / (1 - u1/3)
    mu = np.sqrt(np.clip(1.0 - d[inside] ** 2, 0.0, 1.0))
    ld_factor = (1.0 - u1 * (1.0 - mu)) / (1.0 - u1 / 3.0)
    flux[inside] = 1.0 - (r2**2) * ld_factor

    # 2. Ingress / Egress partial overlap: 1 - k < d < 1 + k
    overlap = (d > (r1 - r2)) & (d < (r1 + r2))
    if np.any(overlap):
        d_ov = d[overlap]
        arg1 = np.clip((d_ov**2 + r2**2 - r1**2) / (2.0 * d_ov * r2), -1.0, 1.0)
        arg2 = np.clip((d_ov**2 + r1**2 - r2**2) / (2.0 * d_ov * r1), -1.0, 1.0)
        part1 = r2**2 * np.arccos(arg1)
        part2 = r1**2 * np.arccos(arg2)
        part3 = 0.5 * np.sqrt(np.clip(4.0 * d_ov**2 * r1**2 - (d_ov**2 + r1**2 - r2**2) ** 2, 0.0, None))
        area = part1 + part2 - part3
        mu_ov = np.sqrt(np.clip(1.0 - np.minimum(d_ov, 1.0) ** 2, 0.0, 1.0))
        ld_factor_ov = (1.0 - u1 * (1.0 - mu_ov)) / (1.0 - u1 / 3.0)
        flux[overlap] = 1.0 - (area / np.pi) * ld_factor_ov

    return np.clip(flux, 0.0, 1.0)


class SkyViewWidget(pg.PlotWidget):
    """Observer-frame sky projection showing star, impact-parameter chord, and moving planet."""

    HALF_SPAN = 2.4

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setBackground(BACKGROUND_COLOR)
        self.setAspectLocked(True)
        self.setMouseEnabled(False, False)
        self.hideAxis("left")
        self.hideAxis("bottom")
        self.setRange(
            xRange=(-self.HALF_SPAN, self.HALF_SPAN),
            yRange=(-self.HALF_SPAN, self.HALF_SPAN),
            padding=0,
        )

        # Star disc (radius = 1.0)
        self._star = QGraphicsEllipseItem(-1.0, -1.0, 2.0, 2.0)
        self._star.setPen(pg.mkPen(BORDER_COLOR, width=1.5, cosmetic=True))
        self._star.setZValue(1)
        self.addItem(self._star)

        # Star limb-darkening ring
        self._limb_ring = QGraphicsEllipseItem(-0.99, -0.99, 1.98, 1.98)
        self._limb_ring.setPen(pg.mkPen(QColor(0, 0, 0, 90), width=2.0, cosmetic=True))
        self._limb_ring.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self._limb_ring.setZValue(2)
        self.addItem(self._limb_ring)

        # Transit chord line
        self._chord = QGraphicsLineItem(-self.HALF_SPAN, 0.0, self.HALF_SPAN, 0.0)
        self._chord.setPen(pg.mkPen(MUTED_TEXT, width=1.5, style=Qt.PenStyle.DashLine, cosmetic=True))
        self._chord.setZValue(3)
        self.addItem(self._chord)

        # Planet disc
        self._planet_k = 0.1
        self._planet = QGraphicsEllipseItem(0.0, 0.0, 0.2, 0.2)
        self._planet.setBrush(QBrush(QColor("#0d1117")))
        self._planet.setPen(pg.mkPen(PLANET_ACCENT, width=1.5, cosmetic=True))
        self._planet.setZValue(10)
        self.addItem(self._planet)

        # Ingress / Egress contact indicators
        self._info_text = pg.TextItem("", color=MUTED_TEXT, anchor=(0.0, 1.0))
        self._info_text.setFont(QFont("Segoe UI", 9))
        self._info_text.setPos(-self.HALF_SPAN + 0.1, -self.HALF_SPAN + 0.2)
        self._info_text.setZValue(20)
        self.addItem(self._info_text)

        self.set_star_color("#ffebdb")

    def set_star_color(self, hex_color: str):
        self._star.setBrush(QBrush(QColor(hex_color)))

    def configure_geometry(self, k: float, b: float):
        self._planet_k = max(0.01, float(k))
        self._chord.setLine(-self.HALF_SPAN, b, self.HALF_SPAN, b)
        self.update_planet_position(0.0, b)

    def update_planet_position(self, x: float, b: float):
        k = self._planet_k
        self._planet.setRect(x - k, b - k, 2.0 * k, 2.0 * k)
        d = math.sqrt(x**2 + b**2)
        if d <= 1.0 - k:
            state = "Full Transit (In-Depth)"
        elif d < 1.0 + k:
            state = "Ingress / Egress Boundary"
        else:
            state = "Out of Transit"
        self._info_text.setText(f"Planet Position: x={x:+.3f} R★, y={b:+.3f} R★ | {state}")


class TransitLightCurveWidget(pg.PlotWidget):
    """Synchronized geometric flux light curve with real-time tracking line."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setBackground(BACKGROUND_COLOR)
        self.showGrid(x=True, y=True, alpha=0.25)
        self.setLabel("bottom", "Relative Projected Coordinate x / R★")
        self.setLabel("left", "Relative Flux F / F₀")
        self.getPlotItem().setContentsMargins(10, 10, 10, 10)

        self._curve = self.plot(
            pen=pg.mkPen(PLANET_ACCENT, width=2.5),
            name="Geometric Transit Profile",
        )
        self._cursor = pg.InfiniteLine(
            pos=0.0,
            angle=90,
            pen=pg.mkPen("#ebcb8b", width=1.5, style=Qt.PenStyle.DashLine),
            movable=False,
        )
        self.addItem(self._cursor)

        self._baseline_line = pg.InfiniteLine(
            pos=1.0,
            angle=0,
            pen=pg.mkPen("#4c566a", width=1.0, style=Qt.PenStyle.DotLine),
            movable=False,
        )
        self.addItem(self._baseline_line)

    def set_data(self, x_grid: np.ndarray, flux_grid: np.ndarray):
        self._curve.setData(x_grid, flux_grid)
        min_y = float(np.min(flux_grid))
        pad = max(1e-4, (1.0 - min_y) * 0.15)
        self.setYRange(min_y - pad, 1.0 + pad * 0.5, padding=0)
        self.setXRange(float(x_grid[0]), float(x_grid[-1]), padding=0)

    def set_cursor_pos(self, x: float):
        self._cursor.setPos(x)


class TransitVisualizerPage(QWidget):
    """Complete Transit & Orbit Simulation workspace page."""

    apply_to_comparisons_requested = Signal(str)

    def __init__(self, on_apply_preset: Optional[Callable[[str], None]] = None, parent=None):
        super().__init__(parent=parent)
        self._on_apply_preset = on_apply_preset
        self._timer = QTimer(self)
        self._timer.setInterval(25)  # 40 fps
        self._timer.timeout.connect(self._on_tick)

        self._is_playing = False
        self._speed_multiplier = 1.0
        self._current_x = -2.0
        self._x_span = 2.0
        self._x_grid = np.linspace(-2.2, 2.2, 500)
        self._flux_grid = np.ones_like(self._x_grid)

        self._build_ui()
        self._load_preset("wasp-39b")

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 16)
        main_layout.setSpacing(10)

        # 1. Header Banner
        header = QFrame()
        header.setStyleSheet("background-color: #252a34; border-radius: 6px; padding: 10px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(4, 4, 4, 4)
        h_layout.setSpacing(4)

        title = QLabel("🔭 Geometric Transit & Orbit Simulation")
        title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #eceff4;")
        subtitle = QLabel(
            "Educational and model-exploration simulator: Visualizes star-planet scale (R_p / R_star)^2, "
            "impact parameter b = (a cos i) / R_star, and geometric obscuration. In transmission spectroscopy, "
            "atmospheric scale height H adds a subtle wavelength-dependent transit depth modulation "
            "ΔD(λ) ≈ 2 H R_p / R_star^2 (typically 100–500 ppm) across this baseline."
        )
        subtitle.setStyleSheet("color: #9aa7b8; font-size: 9.5pt;")
        subtitle.setWordWrap(True)
        h_layout.addWidget(title)
        h_layout.addWidget(subtitle)
        main_layout.addWidget(header)

        # 2. Main split view: Visualizer on top / left, controls on bottom / right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left / Center: Visual Views (Sky View + Light Curve)
        vis_container = QWidget()
        vis_layout = QVBoxLayout(vis_container)
        vis_layout.setContentsMargins(0, 0, 0, 0)
        vis_layout.setSpacing(8)

        # Observer sky view
        self.sky_view = SkyViewWidget()
        self.sky_view.setMinimumHeight(320)
        vis_layout.addWidget(self.sky_view, 3)

        # Light curve plot
        self.light_curve = TransitLightCurveWidget()
        self.light_curve.setMinimumHeight(200)
        vis_layout.addWidget(self.light_curve, 2)

        # Scrubbing slider and play controls
        timeline_bar = QFrame()
        timeline_bar.setStyleSheet("background-color: #252a34; border-radius: 6px; padding: 6px;")
        t_layout = QHBoxLayout(timeline_bar)
        t_layout.setContentsMargins(8, 4, 8, 4)
        t_layout.setSpacing(10)

        self.play_button = QPushButton("▶ Play")
        self.play_button.setFixedWidth(80)
        self.play_button.setStyleSheet(
            "QPushButton { background-color: #88c0d0; color: #181b21; font-weight: bold; border-radius: 4px; padding: 6px; } "
            "QPushButton:hover { background-color: #81a1c1; }"
        )
        self.play_button.clicked.connect(self._toggle_playback)
        t_layout.addWidget(self.play_button)

        self.phase_slider = QSlider(Qt.Orientation.Horizontal)
        self.phase_slider.setRange(-220, 220)
        self.phase_slider.setValue(int(self._current_x * 100))
        self.phase_slider.valueChanged.connect(self._on_slider_moved)
        t_layout.addWidget(self.phase_slider, 1)

        self.speed_selector = QComboBox()
        self.speed_selector.addItems(["Speed: 0.5x", "Speed: 1.0x", "Speed: 2.0x", "Speed: 4.0x"])
        self.speed_selector.setCurrentIndex(1)
        self.speed_selector.currentIndexChanged.connect(self._on_speed_changed)
        t_layout.addWidget(self.speed_selector)

        vis_layout.addWidget(timeline_bar)
        splitter.addWidget(vis_container)

        # Right side: Parameters and Controls
        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setStyleSheet("background-color: #1e222b; border: 1px solid #2e3440; border-radius: 6px;")
        controls_scroll.setFixedWidth(370)

        controls_inner = QWidget()
        c_layout = QVBoxLayout(controls_inner)
        c_layout.setContentsMargins(12, 12, 12, 12)
        c_layout.setSpacing(10)

        c_title = QLabel("System Parameters")
        c_title.setStyleSheet("font-size: 11pt; font-weight: bold; color: #eceff4;")
        c_layout.addWidget(c_title)

        # Planet preset
        c_layout.addWidget(QLabel("Planet Preset:"))
        self.preset_combo = QComboBox()
        for p in PLANET_PRESETS:
            self.preset_combo.addItem(p.planet_name, p.preset_id)
        self.preset_combo.addItem("Custom Parameters", "custom")
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        c_layout.addWidget(self.preset_combo)

        def _make_stepper(spinbox: QDoubleSpinBox, label_text: str):
            row = QHBoxLayout()
            row.addWidget(QLabel(label_text), 1)
            btn_minus = QPushButton("−")
            btn_minus.setFixedSize(28, 28)
            btn_minus.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 0px;")
            btn_minus.setToolTip(f"Decrease {label_text}")
            btn_minus.clicked.connect(lambda: spinbox.setValue(spinbox.value() - spinbox.singleStep()))
            btn_plus = QPushButton("+")
            btn_plus.setFixedSize(28, 28)
            btn_plus.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 0px;")
            btn_plus.setToolTip(f"Increase {label_text}")
            btn_plus.clicked.connect(lambda: spinbox.setValue(spinbox.value() + spinbox.singleStep()))
            spinbox.setMinimumWidth(85)
            row.addWidget(btn_minus)
            row.addWidget(spinbox)
            row.addWidget(btn_plus)
            return row

        # Impact parameter b
        self.b_spin = QDoubleSpinBox()
        self.b_spin.setRange(0.0, 0.98)
        self.b_spin.setSingleStep(0.05)
        self.b_spin.setValue(0.45)
        self.b_spin.valueChanged.connect(self._recalculate_model)
        c_layout.addLayout(_make_stepper(self.b_spin, "Impact parameter b:"))

        # Star radius
        self.rstar_spin = QDoubleSpinBox()
        self.rstar_spin.setRange(0.1, 5.0)
        self.rstar_spin.setSingleStep(0.05)
        self.rstar_spin.setValue(0.895)
        self.rstar_spin.valueChanged.connect(self._recalculate_model)
        c_layout.addLayout(_make_stepper(self.rstar_spin, "Star radius (R☉):"))

        # Planet radius
        self.rpl_spin = QDoubleSpinBox()
        self.rpl_spin.setRange(0.05, 3.0)
        self.rpl_spin.setSingleStep(0.05)
        self.rpl_spin.setValue(1.279)
        self.rpl_spin.valueChanged.connect(self._recalculate_model)
        c_layout.addLayout(_make_stepper(self.rpl_spin, "Planet radius (R_Jup):"))

        # Star temperature
        self.teff_spin = QDoubleSpinBox()
        self.teff_spin.setRange(2000.0, 20000.0)
        self.teff_spin.setSingleStep(100.0)
        self.teff_spin.setValue(5400.0)
        self.teff_spin.valueChanged.connect(self._on_teff_changed)
        c_layout.addLayout(_make_stepper(self.teff_spin, "Star Teff (K):"))

        # Computed geometric quantities
        c_layout.addWidget(QLabel("Geometric Quantities:"))
        self.metrics_label = QLabel()
        self.metrics_label.setStyleSheet(
            "background-color: #252a34; color: #eceff4; border: 1px solid #3b4252; "
            "border-radius: 4px; padding: 8px; font-family: 'Consolas', monospace; font-size: 9pt;"
        )
        c_layout.addWidget(self.metrics_label)

        # Action: Send to comparisons
        self.apply_button = QPushButton("Open in Comparisons Workspace ➔")
        self.apply_button.setStyleSheet(
            "QPushButton { background-color: #5e81ac; color: white; font-weight: bold; border-radius: 4px; padding: 8px; } "
            "QPushButton:hover { background-color: #81a1c1; }"
        )
        self.apply_button.clicked.connect(self._on_apply_clicked)
        c_layout.addWidget(self.apply_button)

        c_layout.addStretch(1)
        controls_scroll.setWidget(controls_inner)
        splitter.addWidget(controls_scroll)

        main_layout.addWidget(splitter, 1)

    def _load_preset(self, preset_id: str):
        try:
            p = get_planet_preset(preset_id)
            r_sun_m = 6.957e8
            r_jup_m = 7.1492e7
            self.rstar_spin.blockSignals(True)
            self.rpl_spin.blockSignals(True)
            self.teff_spin.blockSignals(True)
            self.b_spin.blockSignals(True)

            self.rstar_spin.setValue(p.stellar_radius_m / r_sun_m)
            self.rpl_spin.setValue(p.planet_radius_m / r_jup_m)
            self.teff_spin.setValue(5400.0 if "39" in preset_id else 6000.0)
            self.b_spin.setValue(0.45 if "39" in preset_id else 0.50)

            self.rstar_spin.blockSignals(False)
            self.rpl_spin.blockSignals(False)
            self.teff_spin.blockSignals(False)
            self.b_spin.blockSignals(False)
        except KeyError:
            pass
        self._on_teff_changed()
        self._recalculate_model()

    def _on_preset_selected(self, idx: int):
        preset_id = self.preset_combo.currentData()
        if preset_id != "custom":
            self._load_preset(preset_id)

    def _on_teff_changed(self):
        teff = float(self.teff_spin.value())
        color_hex = teff_to_hex(teff)
        self.sky_view.set_star_color(color_hex)

    def _recalculate_model(self):
        r_sun_m = 6.957e8
        r_jup_m = 7.1492e7
        r_star_m = float(self.rstar_spin.value()) * r_sun_m
        r_pl_m = float(self.rpl_spin.value()) * r_jup_m
        b = float(self.b_spin.value())

        k = r_pl_m / r_star_m
        geom_depth = k**2

        # Recalculate analytic light curve
        self._flux_grid = compute_geometric_transit_flux(self._x_grid, b=b, k=k)
        self.light_curve.set_data(self._x_grid, self._flux_grid)
        self.sky_view.configure_geometry(k=k, b=b)

        # Update labels
        depth_pct = geom_depth * 100.0
        depth_ppm = geom_depth * 1e6
        cur_d = math.sqrt(self._current_x**2 + b**2)
        cur_flux = float(compute_geometric_transit_flux(np.array([self._current_x]), b=b, k=k)[0])
        cur_drop_pct = (1.0 - cur_flux) * 100.0
        cur_drop_ppm = (1.0 - cur_flux) * 1e6

        self.metrics_label.setText(
            f"Radius Ratio (k = Rp/R★): {k:.4f}\n"
            f"Geometric Depth (k²):   {depth_pct:.3f}%\n"
            f"                      ({depth_ppm:,.0f} ppm)\n"
            f"Current Drop ΔF/F₀:     {cur_drop_pct:.3f}%\n"
            f"                      ({cur_drop_ppm:,.0f} ppm)"
        )
        self.sky_view.update_planet_position(self._current_x, b)
        self.light_curve.set_cursor_pos(self._current_x)

    def _toggle_playback(self):
        self._is_playing = not self._is_playing
        if self._is_playing:
            self.play_button.setText("⏸ Pause")
            self._timer.start()
        else:
            self.play_button.setText("▶ Play")
            self._timer.stop()

    def _on_speed_changed(self, idx: int):
        speeds = [0.5, 1.0, 2.0, 4.0]
        self._speed_multiplier = speeds[idx] if 0 <= idx < len(speeds) else 1.0

    def _on_slider_moved(self, val: int):
        self._current_x = val / 100.0
        b = float(self.b_spin.value())
        self.sky_view.update_planet_position(self._current_x, b)
        self.light_curve.set_cursor_pos(self._current_x)

        # Update metrics instantaneous drop
        k = (float(self.rpl_spin.value()) * 7.1492e7) / (float(self.rstar_spin.value()) * 6.957e8)
        cur_flux = float(compute_geometric_transit_flux(np.array([self._current_x]), b=b, k=k)[0])
        cur_drop_pct = (1.0 - cur_flux) * 100.0
        cur_drop_ppm = (1.0 - cur_flux) * 1e6
        depth_pct = (k**2) * 100.0
        depth_ppm = (k**2) * 1e6

        self.metrics_label.setText(
            f"Radius Ratio (k = Rp/R★): {k:.4f}\n"
            f"Geometric Depth (k²):   {depth_pct:.3f}%\n"
            f"                      ({depth_ppm:,.0f} ppm)\n"
            f"Current Drop ΔF/F₀:     {cur_drop_pct:.3f}%\n"
            f"                      ({cur_drop_ppm:,.0f} ppm)"
        )

    def _on_tick(self):
        step = 0.02 * self._speed_multiplier
        self._current_x += step
        if self._current_x > self._x_span:
            self._current_x = -self._x_span
        self.phase_slider.blockSignals(True)
        self.phase_slider.setValue(int(self._current_x * 100))
        self.phase_slider.blockSignals(False)
        self._on_slider_moved(int(self._current_x * 100))

    def _on_apply_clicked(self):
        preset_id = self.preset_combo.currentData()
        self.apply_to_comparisons_requested.emit(preset_id if preset_id != "custom" else "wasp-39b")
        if self._on_apply_preset:
            self._on_apply_preset(preset_id if preset_id != "custom" else "wasp-39b")
