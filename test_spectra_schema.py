"""Portable schema tests; synthetic coordinates, no import-time GUI or file reads."""
import os
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PySide6.QtWidgets import QApplication
from pyqtgraph import ScatterPlotItem

from ecas.ingestion.csv_importer import WASP39B_SCHEMA
from ecas.models.spectrum import SpectrumData
from ecas.visualization.spectra_plot import SpectraPlot


@pytest.fixture
def plot():
    app = QApplication.instance() or QApplication([])
    widget = SpectraPlot()
    yield widget
    widget.close()


@pytest.mark.parametrize("schema", [WASP39B_SCHEMA, None])
def test_archive_and_canonical_columns_plot_the_same_measurements(plot, schema):
    spectrum = SpectrumData(
        source_file=Path("synthetic-archive.csv"),
        columns=("centralwavelng", "pl_trandep", "wavelength", "signal"),
        rows=({"centralwavelng": 1.25, "pl_trandep": 0.02,
               "wavelength": 1.25, "signal": 0.02},),
    )
    original_rows = tuple(dict(row) for row in spectrum.rows)
    assert plot.load_spectrum(spectrum, schema=schema) is True
    scatters = [item for item in plot.plot_widget.items()
                if isinstance(item, ScatterPlotItem)]
    assert len(scatters) == 1
    x_values, y_values = scatters[0].getData()
    assert list(x_values) == [1.25]
    assert list(y_values) == [0.02]
    assert spectrum.rows == original_rows
    assert spectrum.axis_unit is None and spectrum.signal_unit is None
