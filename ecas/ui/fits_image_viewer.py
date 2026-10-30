"""2D FITS Astronomical Image Viewer dialog for ECAS.

Provides interactive visualization of 2D FITS image extensions (e.g. JWST MIRI
imaging exposures), including multi-plane inspection (SCI, ERR, DQ, AREA),
astronomical display stretches (Linear, Percentile, Asinh, Sqrt, Log10),
scientific summary statistics, pixel coordinate readouts, and clear scientific
disclaimers distinguishing imaging from 1D sampled spectra.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ecas.ingestion.fits_image import (
    FitsImageContainer,
    FitsImagePlane,
    apply_display_stretch,
    compute_plane_statistics,
    read_fits_image_plane,
    scan_fits_image,
)


class FitsImageViewerDialog(QDialog):
    """Interactive desktop viewer for calibrated 2D FITS imaging products."""

    def __init__(
        self,
        container_or_path: FitsImageContainer | str | Path,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("ECAS - 2D FITS Astronomical Image Viewer")
        self.resize(1150, 780)

        if isinstance(container_or_path, FitsImageContainer):
            self.container = container_or_path
        else:
            scanned = scan_fits_image(container_or_path)
            if scanned is None:
                raise ValueError(f"Could not load FITS image container from {container_or_path}")
            self.container = scanned

        self.current_plane: FitsImagePlane | None = None
        self.current_raw_data: np.ndarray | None = None
        self.current_stats: dict[str, Any] = {}

        self._setup_ui()
        self._populate_metadata()
        self._populate_planes()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 1. Scientific banner / disclaimer
        banner = QFrame()
        banner.setFrameShape(QFrame.StyledPanel)
        banner.setStyleSheet(
            "background-color: #2b2b20; border: 1px solid #776600; border-radius: 4px; padding: 6px;"
        )
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(8, 4, 8, 4)
        banner_label = QLabel(
            "<b>2D Astronomical Imaging Product:</b> This file contains spatial brightness measurements "
            "across an optical passband, not a 1D sampled (wavelength vs. signal) spectrum. "
            "It cannot be imported directly into laboratory spectral fitting without explicit calibrated extraction."
        )
        banner_label.setWordWrap(True)
        banner_label.setStyleSheet("color: #eedd88; font-size: 11px;")
        banner_layout.addWidget(banner_label)
        main_layout.addWidget(banner)

        # 2. Main content splitter: Left controls/info, Right ImageView
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, stretch=1)

        # Left panel: controls and metadata
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(10)

        # Observation Summary Group
        obs_group = QGroupBox("Observation Summary")
        obs_form = QFormLayout(obs_group)
        obs_form.setSpacing(6)

        self.lbl_target = QLabel("-")
        self.lbl_product = QLabel("-")
        self.lbl_detector = QLabel("-")
        self.lbl_date = QLabel("-")
        self.lbl_exptime = QLabel("-")
        self.lbl_pipeline = QLabel("-")

        for lbl in (
            self.lbl_target,
            self.lbl_product,
            self.lbl_detector,
            self.lbl_date,
            self.lbl_exptime,
            self.lbl_pipeline,
        ):
            lbl.setStyleSheet("font-weight: bold; color: #ffffff;")
            lbl.setWordWrap(True)

        obs_form.addRow("Target:", self.lbl_target)
        obs_form.addRow("Instrument:", self.lbl_product)
        obs_form.addRow("Detector:", self.lbl_detector)
        obs_form.addRow("Date Obs:", self.lbl_date)
        obs_form.addRow("Exposure:", self.lbl_exptime)
        obs_form.addRow("Pipeline:", self.lbl_pipeline)
        left_layout.addWidget(obs_group)

        # Display Controls Group
        ctrl_group = QGroupBox("Display Controls")
        ctrl_form = QFormLayout(ctrl_group)
        ctrl_form.setSpacing(6)

        self.cmb_plane = QComboBox()
        self.cmb_plane.currentIndexChanged.connect(self._on_plane_changed)
        ctrl_form.addRow("Image Plane:", self.cmb_plane)

        self.cmb_stretch = QComboBox()
        self.cmb_stretch.addItems([
            "Asinh (Astronomical)",
            "Percentile (1% - 99%)",
            "Min - Max (Full Range)",
            "Square Root (Sqrt)",
            "Logarithmic (Log10)",
        ])
        self.cmb_stretch.currentIndexChanged.connect(self._on_stretch_changed)
        ctrl_form.addRow("Stretch:", self.cmb_stretch)

        self.cmb_colormap = QComboBox()
        self.cmb_colormap.addItems(["inferno", "viridis", "plasma", "magma", "cividis", "turbo"])
        self.cmb_colormap.currentIndexChanged.connect(self._on_colormap_changed)
        ctrl_form.addRow("Colormap:", self.cmb_colormap)

        left_layout.addWidget(ctrl_group)

        # Image Statistics Group
        stats_group = QGroupBox("Plane Statistics")
        stats_form = QFormLayout(stats_group)
        stats_form.setSpacing(5)

        self.lbl_dimensions = QLabel("-")
        self.lbl_units = QLabel("-")
        self.lbl_range = QLabel("-")
        self.lbl_median = QLabel("-")
        self.lbl_nan = QLabel("-")

        for lbl in (
            self.lbl_dimensions,
            self.lbl_units,
            self.lbl_range,
            self.lbl_median,
            self.lbl_nan,
        ):
            lbl.setStyleSheet("color: #d0d0d0;")

        stats_form.addRow("Dimensions:", self.lbl_dimensions)
        stats_form.addRow("Physical Unit:", self.lbl_units)
        stats_form.addRow("Range [Min, Max]:", self.lbl_range)
        stats_form.addRow("Median [Std]:", self.lbl_median)
        stats_form.addRow("Bad / NaN Pixels:", self.lbl_nan)
        left_layout.addWidget(stats_group)

        left_layout.addStretch(1)
        splitter.addWidget(left_panel)

        # Right panel: ImageView with mouse position / value bar
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(6)

        # PyQtGraph ImageView
        self.image_view = pg.ImageView()
        # Clean up unnecessary default buttons
        self.image_view.ui.menuBtn.hide()
        self.image_view.ui.roiBtn.hide()

        # Connect mouse moved signal on viewbox
        view_box = self.image_view.getView()
        view_box.scene().sigMouseMoved.connect(self._on_mouse_moved)

        right_layout.addWidget(self.image_view, stretch=1)

        # Pixel readout bar
        self.lbl_cursor = QLabel("Pixel: (X: --, Y: --) | Value: --")
        self.lbl_cursor.setStyleSheet(
            "font-family: monospace; font-size: 11px; padding: 4px; background-color: #1a1a1a; border: 1px solid #333333; border-radius: 3px;"
        )
        right_layout.addWidget(self.lbl_cursor)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # Bottom button bar
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch(1)
        btn_close = QPushButton("Close")
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)
        bottom_bar.addWidget(btn_close)
        main_layout.addLayout(bottom_bar)

    def _populate_metadata(self) -> None:
        c = self.container
        self.lbl_target.setText(c.target_name or "(Unspecified)")
        self.lbl_product.setText(c.product_summary or "(Unspecified)")
        self.lbl_detector.setText(c.detector or "(Unspecified)")
        self.lbl_date.setText(c.date_obs or "(Unspecified)")
        self.lbl_exptime.setText(
            f"{c.exposure_time_sec:.3f} s" if c.exposure_time_sec is not None else "(Unspecified)"
        )
        self.lbl_pipeline.setText(c.pipeline_stage or "Standard Level-2 Product")

    def _populate_planes(self) -> None:
        self.cmb_plane.blockSignals(True)
        self.cmb_plane.clear()

        default_idx = 0
        for i, plane in enumerate(self.container.planes):
            self.cmb_plane.addItem(plane.display_label, userData=plane)
            if plane.extname.upper() == "SCI":
                default_idx = i

        self.cmb_plane.blockSignals(False)
        if self.container.planes:
            self.cmb_plane.setCurrentIndex(default_idx)
            self._load_plane(self.container.planes[default_idx])

    def _on_plane_changed(self, index: int) -> None:
        if index < 0 or index >= len(self.container.planes):
            return
        plane = self.container.planes[index]
        self._load_plane(plane)

    def _load_plane(self, plane: FitsImagePlane) -> None:
        self.current_plane = plane
        try:
            arr = read_fits_image_plane(self.container.path, plane)
        except Exception as exc:
            self.lbl_range.setText(f"Read error: {exc}")
            return

        self.current_raw_data = arr
        self.current_stats = compute_plane_statistics(arr)

        # Update stats UI
        self.lbl_dimensions.setText(f"{plane.width} x {plane.height} pixels (NAXIS1 x NAXIS2)")
        self.lbl_units.setText(plane.bunit or "(unitless / integer bitmask)")
        fmin = self.current_stats["finite_min"]
        fmax = self.current_stats["finite_max"]
        self.lbl_range.setText(f"{fmin:.4g} to {fmax:.4g}")
        med = self.current_stats["median"]
        std = self.current_stats["std"]
        self.lbl_median.setText(f"{med:.4g}  [+- {std:.4g}]")
        nan_ct = self.current_stats["nan_count"]
        tot = self.current_stats["total_pixels"]
        nan_pct = (nan_ct / tot * 100.0) if tot > 0 else 0.0
        self.lbl_nan.setText(f"{nan_ct:,} ({nan_pct:.1f}%)")

        self._render_current_image()

    def _on_stretch_changed(self) -> None:
        self._render_current_image()

    def _on_colormap_changed(self) -> None:
        self._apply_colormap()

    def _apply_colormap(self) -> None:
        cmap_name = self.cmb_colormap.currentText()
        try:
            cmap = pg.colormap.get(cmap_name)
            self.image_view.setColorMap(cmap)
        except Exception:
            pass

    def _render_current_image(self) -> None:
        if self.current_raw_data is None:
            return

        stretch_name = self.cmb_stretch.currentText()
        disp_arr, vmin, vmax = apply_display_stretch(
            self.current_raw_data,
            stretch_name,
            self.current_stats,
        )

        # Pass transpose to align NAXIS1 horizontally (X) and NAXIS2 vertically (Y)
        self.image_view.setImage(
            disp_arr.T,
            autoLevels=False,
            levels=(vmin, vmax),
        )
        self._apply_colormap()

    def _on_mouse_moved(self, scene_pos: QPointF) -> None:
        if self.current_raw_data is None or self.current_plane is None:
            return

        view_box = self.image_view.getView()
        view_pos = view_box.mapSceneToView(scene_pos)
        x = int(np.floor(view_pos.x()))
        y = int(np.floor(view_pos.y()))

        width = self.current_plane.width
        height = self.current_plane.height

        if 0 <= x < width and 0 <= y < height:
            val = self.current_raw_data[y, x]
            unit = f" {self.current_plane.bunit}" if self.current_plane.bunit else ""
            if np.isnan(val):
                val_str = "NaN (Invalid / Blank)"
            elif isinstance(val, (int, np.integer)):
                val_str = f"{val} (0x{val:04X})"
            else:
                val_str = f"{val:.6g}{unit}"
            self.lbl_cursor.setText(f"Pixel: (X: {x}, Y: {y}) | Value: {val_str}")
        else:
            self.lbl_cursor.setText("Pixel: (X: --, Y: --) | Value: --")

