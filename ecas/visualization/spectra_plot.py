
"""Spectral plotting widget using PyQtGraph.

Displays normalized SpectrumData measurements without modifying the source
data. Missing, non-numeric, and non-finite coordinate pairs are excluded.
"""

import math
import os
from pathlib import Path
from typing import Optional

# Ensure PyQtGraph uses the same Qt binding as the ECAS application.
os.environ["PYQTGRAPH_QT_LIB"] = "PySide6"

from PySide6 import QtCore as qtc
from PySide6 import QtGui as qtgui
from PySide6 import QtWidgets as qtw
from pyqtgraph import PlotWidget, ScatterPlotItem


class SpectraPlot(qtw.QWidget):
    """Display a normalized SpectrumData object as a spectral plot."""

    dataset_changed = qtc.Signal(object)

    def __init__(self, parent=None, title="Spectral Data"):
        super().__init__(parent=parent)
        self.setWindowTitle(title)

        layout = qtw.QVBoxLayout(self)
        self.plot_widget = PlotWidget(self)
        layout.addWidget(self.plot_widget)

        # Keep references to the axes and view for labels and scaling.
        self.bottom_axis = self.plot_widget.getAxis("bottom")
        self.left_axis = self.plot_widget.getAxis("left")
        self.viewbox = self.plot_widget.getViewBox()

        # Apply neutral axis styling.
        pen = qtgui.QPen(qtgui.QColor("#888888"))
        self.bottom_axis.setPen(pen)
        self.left_axis.setPen(pen)

        # Initialize state only. Dataset-specific values belong in
        # load_spectrum(), where spectrum_data is actually available.
        self._current_spectrum = None
        self._wavelength_column: Optional[str] = None
        self._signal_column: Optional[str] = None
        self._axis_unit_label: Optional[str] = None
        self._signal_unit_label: Optional[str] = None

    def load_spectrum(self, spectrum_data) -> bool:
        """Plot valid coordinate pairs from a normalized SpectrumData object.

        Returns True if at least one valid point is plotted. Returns False
        and clears the widget if the required columns or valid points are absent.
        """

        # Clear the previous plot before attempting a replacement. A failed
        # load must never leave the previous dataset visible.
        self.clear()

        if spectrum_data is None:
            return False

        # Identify the normalized columns used for the plotted coordinates.
        available_columns = set(spectrum_data.columns)
        self._wavelength_column = (
            "wavelength" if "wavelength" in available_columns else None
        )
        self._signal_column = (
            "signal" if "signal" in available_columns else None
        )

        # Reject data without both required coordinate columns.
        if not (self._wavelength_column and self._signal_column):
            self.reset_on_failure()
            return False

        # Use only units explicitly supplied by SpectrumData.
        self._axis_unit_label = spectrum_data.axis_unit
        self._signal_unit_label = spectrum_data.signal_unit

        # Filter missing, non-numeric, NaN, and infinite coordinate pairs.
        x_vals = []
        y_vals = []

        for row in spectrum_data.rows:
            wavelength = row.get(self._wavelength_column)
            signal = row.get(self._signal_column)

            if wavelength is None or signal is None:
                continue

            try:
                x_value = float(wavelength)
                y_value = float(signal)
            except (TypeError, ValueError, OverflowError):
                continue

            if not (math.isfinite(x_value) and math.isfinite(y_value)):
                continue

            x_vals.append(x_value)
            y_vals.append(y_value)

        # An empty plot must not retain metadata from a failed dataset.
        if not x_vals:
            self.reset_on_failure()
            return False

        # Plot the actual valid measurements; no interpolation is performed.
        scatter = ScatterPlotItem(
            x=x_vals,
            y=y_vals,
            pen=None,
            brush=qtgui.QBrush(qtgui.QColor("steelblue")),
            symbol="o",
            symbolSize=6,
            antialias=True,
        )
        self.plot_widget.addItem(scatter)

        # Show units only when they are known.
        xlabel = self._wavelength_column
        ylabel = self._signal_column

        if self._axis_unit_label:
            xlabel = f"{xlabel} ({self._axis_unit_label})"

        if self._signal_unit_label:
            ylabel = f"{ylabel} ({self._signal_unit_label})"

        self.plot_widget.setLabel("bottom", text=xlabel)
        self.plot_widget.setLabel("left", text=ylabel)

        # Let PyQtGraph scale the axes to the supplied valid measurements.
        # Padding also handles datasets with identical minimum and maximum.
        self.viewbox.setRange(
            xRange=(min(x_vals), max(x_vals)),
            yRange=(min(y_vals), max(y_vals)),
            padding=0.05,
        )

        # Keep the original model object; never modify its rows or metadata.
        self._current_spectrum = spectrum_data
        self.dataset_changed.emit(spectrum_data)
        return True

    def clear(self):
        """Clear the visible plot, labels, and dataset state."""

        self.plot_widget.clear()

        self._current_spectrum = None
        self._wavelength_column = None
        self._signal_column = None
        self._axis_unit_label = None
        self._signal_unit_label = None

        self.plot_widget.setLabel("bottom", text="")
        self.plot_widget.setLabel("left", text="")

    def reset_on_failure(self):
        """Reset all visible and internal state after an unsuccessful load."""

        self.clear()

    def on_view_changed(self):
        """Placeholder for future zoom or pan handling."""
        pass
