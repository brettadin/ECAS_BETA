"""Native-coordinate and wavelength-converted inspection of validated cross sections."""
from PySide6.QtWidgets import QWidget, QVBoxLayout

# Import through the established plotting module to retain its PySide6 binding.
from ecas.visualization.spectra_plot import PlotWidget


def reference_display_points(product, axis_mode: str = 'wavenumber'):
    """Return (axis_label, points) in native cm^-1 or converted strictly increasing microns."""
    if axis_mode not in ('wavenumber', 'microns'):
        raise ValueError(f'Unsupported reference axis_mode: {axis_mode!r}')
    if product is None:
        return ('Wavenumber (cm^-1)' if axis_mode == 'wavenumber' else 'Wavelength (microns)'), ()
    if axis_mode == 'wavenumber':
        return 'Wavenumber (cm^-1)', tuple(getattr(product, 'points', ()))
    converted = [
        (10000.0 / float(nu), val)
        for nu, val in getattr(product, 'points', ())
        if float(nu) > 0.0
    ]
    converted.sort(key=lambda pair: pair[0])
    return 'Wavelength (microns)', tuple(converted)


class ReferencePlot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumHeight(180)
        self.plot_widget = PlotWidget(self)
        self.plot_widget.setMinimumHeight(160)
        layout.addWidget(self.plot_widget)
        self.axis_mode = 'wavenumber'
        self.plot_widget.setLabel('bottom', 'Wavenumber (cm^-1)')
        # Small cross sections must not look like order-one values if a long
        # axis label containing an automatic multiplier gets clipped.
        self.plot_widget.setLabel('left', 'σ (cm²/molecule)')
        self.plot_widget.getAxis('left').enableAutoSIPrefix(False)
        self.curve = self.plot_widget.plot(pen='#81a1c1')
        self.current_product = None

    def set_axis_mode(self, mode: str):
        if mode not in ('wavenumber', 'microns'):
            raise ValueError(f'Unsupported axis_mode: {mode!r}')
        self.axis_mode = mode
        label = 'Wavenumber (cm^-1)' if mode == 'wavenumber' else 'Wavelength (microns)'
        self.plot_widget.setLabel('bottom', label)
        if self.current_product is not None:
            self._render_current()

    def toggle_axis_mode(self) -> str:
        next_mode = 'microns' if self.axis_mode == 'wavenumber' else 'wavenumber'
        self.set_axis_mode(next_mode)
        return next_mode

    def _render_current(self):
        if self.current_product is None:
            self.curve.setData([], [])
            return
        label, pts = reference_display_points(self.current_product, self.axis_mode)
        self.plot_widget.setLabel('bottom', label)
        self.curve.setData([point[0] for point in pts], [point[1] for point in pts])
        self.plot_widget.enableAutoRange()

    def load_product(self, product):
        """Draw the validated sample coordinates on linear native or converted axes."""
        self.current_product = product
        self._render_current()

    def clear(self):
        self.curve.setData([], [])
        self.current_product = None

    def zoom_in(self):
        """Zoom in by 20% on both axes."""
        self.plot_widget.getViewBox().scaleBy((0.8, 0.8))

    def zoom_out(self):
        """Zoom out by 25% on both axes."""
        self.plot_widget.getViewBox().scaleBy((1.25, 1.25))

    def reset_view(self):
        """Reset view range to fit all plotted reference points."""
        self.plot_widget.getViewBox().autoRange()

    def set_wheel_zoom_enabled(self, enabled: bool):
        """Toggle mouse-wheel zoom on the plot widget."""
        self.plot_widget.wheel_zoom_enabled = enabled
