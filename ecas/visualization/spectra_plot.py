
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
from pyqtgraph import PlotWidget as _PGPlotWidget, ScatterPlotItem


class PlotWidget(_PGPlotWidget):
    """PyQtGraph PlotWidget that prevents accidental zooming when scrolling a page.

    By default, mouse wheel events without modifier keys are ignored and bubble up
    to the parent scroll area, ensuring uninterrupted workspace page navigation.
    To zoom using the mouse wheel, hold Ctrl while scrolling, or toggle wheel zoom.
    Intentional zoom controls (Zoom In, Zoom Out, Auto-range) are also provided.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wheel_zoom_enabled = False

    def wheelEvent(self, ev):
        if self.wheel_zoom_enabled or bool(ev.modifiers() & qtc.Qt.KeyboardModifier.ControlModifier):
            super().wheelEvent(ev)
        else:
            ev.ignore()


class SpectraPlot(qtw.QWidget):
    """Display a normalized SpectrumData object as a spectral plot."""

    dataset_changed = qtc.Signal(object)

    def __init__(self, parent=None, title="Spectral Data"):
        super().__init__(parent=parent)
        self.setWindowTitle(title)

        layout = qtw.QVBoxLayout(self)
        self.setMinimumHeight(180)
        self.plot_widget = PlotWidget(self)
        self.plot_widget.setMinimumHeight(160)
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

    def load_spectrum(self, spectrum_data, schema=None) -> bool:
        """Plot valid coordinate pairs from a normalized SpectrumData object.

        Returns True if at least one valid point is plotted. Returns False
        and clears the widget if the required columns or valid points are absent.
        The 'schema' argument is used to override column name detection for
        archive schemas like WASP-39 b, which use non-standard column names.

        Args:
            spectrum_data: The SpectrumData object containing normalized data.
            schema: Optional schema dict mapping ECAS canonical names to source columns.
                    If None, generic column name detection is used.
        """

        # Clear the previous plot before attempting a replacement. A failed
        # load must never leave the previous dataset visible.
        self.clear()

        if spectrum_data is None:
            return False

        # Determine wavelength and signal columns based on schema.
        available_columns = set(spectrum_data.columns)

        if schema is not None and len(schema) == 2:
            # Archive schema provides direct mapping from ECAS canonical names.
            self._wavelength_column = schema.get("wavelength")
            self._signal_column = schema.get("signal")
        else:
            # Generic mode uses simple heuristic for common column names.
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

    def zoom_in(self):
        """Zoom in by 20% on both axes."""
        self.viewbox.scaleBy((0.8, 0.8))

    def zoom_out(self):
        """Zoom out by 25% on both axes."""
        self.viewbox.scaleBy((1.25, 1.25))

    def reset_view(self):
        """Reset view range to fit all plotted data points."""
        self.viewbox.autoRange()

    def set_wheel_zoom_enabled(self, enabled: bool):
        """Toggle mouse-wheel zoom on the plot widget."""
        self.plot_widget.wheel_zoom_enabled = enabled

    def on_view_changed(self):
        """Placeholder for future zoom or pan handling."""
        pass
