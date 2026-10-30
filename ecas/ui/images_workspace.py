"""2D FITS Images workspace for ECAS.

Provides a dedicated workspace for inspecting 2D FITS astronomical images
(such as JWST MIRI imaging products), with plane selection, display stretch,
color maps, surface brightness readout, and zoom/pan navigation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ecas.ingestion.fits_image import (
    FitsImageContainer,
    FitsImagePlane,
    scan_fits_image,
)
from ecas.ui.fits_image_viewer import FitsImageViewerWidget


class FitsImageCanvas(QWidget):
    """Backwards-compatible wrapper around PyQtGraph image canvas."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.image_view = pg.ImageView()
        layout.addWidget(self.image_view)


class ImagesWorkspacePage(QWidget):
    """First-class workspace for inspecting 2D FITS astronomical images."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header card
        header = QFrame()
        header.setStyleSheet(
            "background-color: #242933; border: 1px solid #3b4252; border-radius: 6px; padding: 8px;"
        )
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(8, 6, 8, 6)

        title = QLabel("<b>Images — 2D FITS Astronomical Image Viewer</b>")
        title.setStyleSheet("color: #88c0d0; font-size: 14pt; font-weight: 600;")
        h_layout.addWidget(title)

        desc = QLabel(
            "Inspect spatial image planes, surface brightness, calibrated pixel values, and detector masks from 2D FITS products "
            "(e.g. JWST MIRI imaging).<br/>"
            "<b>Scientific Notice:</b> 2D FITS image pixels represent spatial detector counts or surface brightness; "
            "they are not 1D exoplanet transmission spectra and do not establish molecular presence directly."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #d8dee9; font-size: 10pt; line-height: 1.3;")
        h_layout.addWidget(desc)
        layout.addWidget(header)

        # Top controls toolbar
        toolbar = QHBoxLayout()
        self.open_button = QPushButton("📂 Open 2D FITS Image…")
        self.open_button.setStyleSheet(
            "QPushButton { background-color: #5e81ac; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px; } "
            "QPushButton:hover { background-color: #81a1c1; }"
        )
        self.open_button.clicked.connect(self._on_open_file)
        toolbar.addWidget(self.open_button)

        self.zoom_in_btn = QPushButton("🔍+")
        self.zoom_in_btn.setToolTip("Zoom in on image")
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        self.zoom_out_btn = QPushButton("🔍-")
        self.zoom_out_btn.setToolTip("Zoom out on image")
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        self.reset_zoom_btn = QPushButton("↺ Reset View")
        self.reset_zoom_btn.setToolTip("Reset zoom and auto-fit image")
        self.reset_zoom_btn.clicked.connect(self._reset_zoom)
        toolbar.addWidget(self.zoom_in_btn)
        toolbar.addWidget(self.zoom_out_btn)
        toolbar.addWidget(self.reset_zoom_btn)

        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        # Core Viewer Widget
        self.viewer = FitsImageViewerWidget(parent=self)
        layout.addWidget(self.viewer, 1)

    @property
    def stretch_selector(self) -> QComboBox:
        return self.viewer.cmb_stretch

    @property
    def colormap_selector(self) -> QComboBox:
        return self.viewer.cmb_colormap

    @property
    def plane_selector(self) -> QComboBox:
        return self.viewer.cmb_plane

    @property
    def container(self) -> FitsImageContainer | None:
        return self.viewer.container

    @property
    def current_plane(self) -> FitsImagePlane | None:
        return self.viewer.current_plane

    @property
    def canvas(self) -> QWidget:
        return self.viewer

    def load_fits_image(self, file_path_or_container: str | Path | FitsImageContainer) -> bool:
        """Load a 2D FITS container and display its primary image plane."""
        success = self.viewer.load_fits_image(file_path_or_container)
        if not success:
            QMessageBox.warning(
                self,
                "Invalid 2D FITS Image",
                "The selected file does not contain valid 2D FITS image planes.",
            )
        return success

    def _zoom_in(self) -> None:
        self.viewer.zoom(1.25)

    def _zoom_out(self) -> None:
        self.viewer.zoom(0.8)

    def _reset_zoom(self) -> None:
        self.viewer.reset_view()

    def _on_open_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open 2D FITS Astronomical Image",
            "",
            "FITS Images (*.fits *.fit *.fts);;All Files (*)",
        )
        if file_path:
            self.load_fits_image(file_path)
