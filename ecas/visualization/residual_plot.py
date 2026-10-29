"""Aligned overlay and residual plot widget for eligible ResidualDiagnostic results."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from ecas.comparison.residuals import ResidualDiagnostic
from ecas.visualization.spectra_plot import PlotWidget


class ResidualPlot(QWidget):
    """Display aligned input overlay and left-minus-right residuals in shared units."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        layout.addWidget(splitter)

        self.overlay_widget = PlotWidget(self)
        self.overlay_widget.getAxis('left').enableAutoSIPrefix(False)
        self.left_curve = self.overlay_widget.plot(pen='#88c0d0', name='Left input')
        self.right_curve = self.overlay_widget.plot(pen='#ebcb8b', name='Right input')

        self.residual_widget = PlotWidget(self)
        self.residual_widget.getAxis('left').enableAutoSIPrefix(False)
        self.zero_curve = self.residual_widget.plot(pen='#4c566a')
        self.residual_curve = self.residual_widget.plot(pen='#bf616a', name='Residual')

        splitter.addWidget(self.overlay_widget)
        splitter.addWidget(self.residual_widget)

        self.current_diagnostic = None
        self._reset_labels()

    def _reset_labels(self):
        self.overlay_widget.setLabel('bottom', 'Coordinate')
        self.overlay_widget.setLabel('left', 'Signal')
        self.residual_widget.setLabel('bottom', 'Coordinate')
        self.residual_widget.setLabel('left', 'Residual (left - right)')

    def load_diagnostic(self, diagnostic: ResidualDiagnostic):
        """Plot aligned curves and residuals from a verified ResidualDiagnostic."""
        self.clear()
        if not isinstance(diagnostic, ResidualDiagnostic) or diagnostic.eligibility.status != 'eligible':
            raise ValueError('ResidualPlot requires an eligible ResidualDiagnostic')

        x = list(diagnostic.coordinates)
        self.overlay_widget.setLabel('bottom', f'Wavelength ({diagnostic.axis_unit})')
        self.overlay_widget.setLabel('left', f'{diagnostic.observable} ({diagnostic.signal_unit})')
        self.residual_widget.setLabel('bottom', f'Wavelength ({diagnostic.axis_unit})')
        self.residual_widget.setLabel(
            'left', f'Residual left - right ({diagnostic.signal_unit})'
        )

        self.left_curve.setData(x, list(diagnostic.left_values))
        self.right_curve.setData(x, list(diagnostic.right_values))
        self.zero_curve.setData([x[0], x[-1]], [0.0, 0.0])
        self.residual_curve.setData(x, list(diagnostic.residuals))

        self.overlay_widget.enableAutoRange()
        self.residual_widget.enableAutoRange()
        self.current_diagnostic = diagnostic

    def clear(self):
        self.left_curve.setData([], [])
        self.right_curve.setData([], [])
        self.zero_curve.setData([], [])
        self.residual_curve.setData([], [])
        self.current_diagnostic = None
        self._reset_labels()

