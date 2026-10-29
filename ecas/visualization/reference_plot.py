"""Native-coordinate inspection of validated calculated cross sections."""
from PySide6.QtWidgets import QWidget, QVBoxLayout

# Import through the established plotting module to retain its PySide6 binding.
from ecas.visualization.spectra_plot import PlotWidget


class ReferencePlot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.plot_widget = PlotWidget(self)
        layout.addWidget(self.plot_widget)
        self.plot_widget.setLabel('bottom', 'Wavenumber (cm^-1)')
        # Small cross sections must not look like order-one values if a long
        # axis label containing an automatic multiplier gets clipped.
        self.plot_widget.setLabel('left', 'σ (cm²/molecule)')
        self.plot_widget.getAxis('left').enableAutoSIPrefix(False)
        self.curve = self.plot_widget.plot(pen='#81a1c1')
        self.current_product = None

    def load_product(self, product):
        """Draw the validated sample coordinates unchanged, on linear native axes."""
        self.curve.setData([point[0] for point in product.points],
                           [point[1] for point in product.points])
        self.plot_widget.enableAutoRange()
        self.current_product = product

    def clear(self):
        self.curve.setData([], [])
        self.current_product = None
