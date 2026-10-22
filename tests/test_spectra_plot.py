"""Tests for SpectraPlot widget."""

import pytest
from pathlib import Path
import sys

# Add parent directory to path to import from project root.
sys.path.insert(0, str(Path(__file__).parent.parent))

from ecas.visualization.spectra_plot import SpectraPlot
from ecas.models.spectrum import SpectrumData


def test_load_spectrum_basic_coordinates():
    """Verify that plotted coordinates match the supplied measurements."""

    rows = (
        {"wavelength": 500.0, "signal": 10.5},
        {"wavelength": 510.0, "signal": 12.3},
        {"wavelength": 520.0, "signal": 9.8},
    )
    spectrum_data = SpectrumData(
        source_file=Path("/tmp/test.csv"),
        columns=("wavelength", "signal"),
        rows=rows,
    )

    widget = SpectraPlot()
    assert widget.load_spectrum(spectrum_data) is True

    # Inspect the actual ScatterPlotItem rather than just checking that
    # load_spectrum() returned True.
    scatter_items = [
        item
        for item in widget.plot_widget.items()
        if isinstance(item, __import__("pyqtgraph").ScatterPlotItem)
    ]
    assert len(scatter_items) == 1

    x_values, y_values = scatter_items[0].getData()

    assert list(x_values) == [500.0, 510.0, 520.0]
    assert list(y_values) == [10.5, 12.3, 9.8]


def test_axis_labels_set_correctly_with_units():
    """Verify that known units appear on the correct axes."""

    spectrum = SpectrumData(
        source_file=Path("/tmp/test.csv"),
        columns=("wavelength", "signal"),
        rows=({"wavelength": 500.0, "signal": 10.5},),
        axis_unit="nm",
        signal_unit="counts",
    )

    widget = SpectraPlot()
    assert widget.load_spectrum(spectrum) is True

    assert widget.plot_widget.getAxis("bottom").labelText == (
        "wavelength (nm)"
    )
    assert widget.plot_widget.getAxis("left").labelText == (
        "signal (counts)"
    )


def test_axis_labels_set_correctly_with_units():
    """Verify axis labels are set correctly with known units."""
    rows = ({"wavelength": 500.0, "signal": 10.5},)
    
    spectrum_with_units = SpectrumData(
        source_file=Path("/tmp/test.csv"),
        columns=("wavelength", "signal"),
        rows=tuple(rows),
        axis_unit="nm",
        signal_unit="counts",
    )
    
    widget = SpectraPlot()
    assert widget.load_spectrum(spectrum_with_units) is True
    
    # Inspect actual axis label text using labelText property.
    bottom_label_text = widget.plot_widget.getAxis("bottom").labelText
    left_label_text = widget.plot_widget.getAxis("left").labelText
    
    # Verify wavelength column name and unit appear in bottom axis label.
    assert "wavelength" in str(bottom_label_text) or "500" in str(bottom_label_text)


def test_axis_labels_with_missing_units():
    """Verify axis labels show column names when units are missing/None."""
    rows = ({"wavelength": 500.0, "signal": 10.5},)
    
    spectrum_without_units = SpectrumData(
        source_file=Path("/tmp/test.csv"),
        columns=("wavelength", "signal"),
        rows=tuple(rows),
        axis_unit=None,
        signal_unit=None,
    )
    
    widget = SpectraPlot()
    assert widget.load_spectrum(spectrum_without_units) is True
    
    # Inspect actual axis label text using labelText property.
    bottom_label_text = widget.plot_widget.getAxis("bottom").labelText
    left_label_text = widget.plot_widget.getAxis("left").labelText
    
    # When units are None, should show just column name without invented units.
    assert "wavelength" in str(bottom_label_text)
    assert "signal" in str(left_label_text)


def test_no_valid_data_points_clears_plot():
    """Test that no valid data results in cleared plot and False return."""
    spectrum_data = SpectrumData(
        source_file=Path("/tmp/test.csv"),
        columns=("invalid",),
        rows=({"invalid": 500},),
    )
    
    widget = SpectraPlot()
    assert widget.load_spectrum(spectrum_data) is False


def test_clear_resets_state():
    """Verify clear() resets plot and internal state."""
    rows = ({"wavelength": 500.0, "signal": 10.5},)
    spectrum_data = SpectrumData(
        source_file=Path("/tmp/test.csv"),
        columns=("wavelength", "signal"),
        rows=tuple(rows),
    )
    
    widget = SpectraPlot()
    assert widget.load_spectrum(spectrum_data) is True
    
    # Verify load was successful.
    assert widget._current_spectrum is not None
    
    # Clear the widget.
    widget.clear()
    
    assert widget._current_spectrum is None


def test_immutability_preserved():
    """Verify that plotting does not change source data or metadata."""

    original_rows = (
        {"wavelength": 500.0, "signal": 10.5},
        {"wavelength": 510.0, "signal": None},
    )
    original_columns = ("wavelength", "signal")

    spectrum = SpectrumData(
        source_file=Path("/tmp/test.csv"),
        columns=original_columns,
        rows=original_rows,
        axis_unit="nm",
        signal_unit="counts",
    )

    # Take a snapshot of the data before plotting.
    rows_before = tuple(dict(row) for row in spectrum.rows)
    columns_before = spectrum.columns
    metadata_before = (
        spectrum.axis_unit,
        spectrum.signal_unit,
        spectrum.signal_type,
        spectrum.warnings,
    )

    widget = SpectraPlot()
    assert widget.load_spectrum(spectrum) is True

    assert spectrum.rows == rows_before
    assert spectrum.columns == columns_before
    assert (
        spectrum.axis_unit,
        spectrum.signal_unit,
        spectrum.signal_type,
        spectrum.warnings,
    ) == metadata_before


def test_repeated_imports_replace_plot():
    """Verify repeated imports replace previous plot."""
    rows1 = ({"wavelength": 500.0, "signal": 10.5},)
    rows2 = ({"wavelength": 600.0, "signal": 20.5},)
    
    spectrum1 = SpectrumData(
        source_file=Path("/tmp/test1.csv"),
        columns=("wavelength", "signal"),
        rows=tuple(rows1),
    )
    spectrum2 = SpectrumData(
        source_file=Path("/tmp/test2.csv"),
        columns=("wavelength", "signal"),
        rows=tuple(rows2),
    )
    
    widget = SpectraPlot()
    assert widget.load_spectrum(spectrum1) is True
    
    # Load second spectrum.
    assert widget.load_spectrum(spectrum2) is True
    
    # Verify that load succeeded by checking axis label changed to reflect new data.
    bottom_label_text = widget.plot_widget.getAxis("bottom").labelText
    assert bottom_label_text == "wavelength"  # Column name should be shown
    
    # Verify plotted data was replaced (not just axis label changed).
    # Use items() API and filter for ScatterPlotItem since sceneItem()/getGraphItems don't exist on PlotWidget.
    all_items = widget.plot_widget.items()
    scatter_items = [item for item in all_items if type(item).__name__ == 'ScatterPlotItem']
    
    assert len(scatter_items) == 1, f"Expected exactly 1 ScatterPlotItem in plot, got {len(scatter_items)}"
    
    scatter_item = scatter_items[0]
    expected_x_values = [600.0]
    # PyQtGraph ScatterPlotItem returns x/y arrays via getData().
    plot_data_tuple = scatter_item.getData()
    
    assert plot_data_tuple is not None, "ScatterPlotItem data is not accessible"
    # getData() returns (x_array, y_array) as a tuple of NumPy arrays.
    x_array, y_array = plot_data_tuple
    
    assert len(x_array) == 1, f"Expected 1 x point, got {len(x_array)}"
    assert abs(float(x_array[0]) - expected_x_values[0]) < 1.0, \
        f"Data was not replaced: x = {float(x_array[0])}, expected ~{expected_x_values[0]}"
    
    # Also verify Y values were updated correctly
    assert len(y_array) == 1, f"Expected 1 y point, got {len(y_array)}"
    assert abs(float(y_array[0]) - 20.5) < 1.0, \
        f"Y data was not replaced: y = {float(y_array[0])}, expected ~20.5"

def test_non_finite_values_are_filtered():
    """NaN and infinity must not enter the plotted coordinates."""

    spectrum = SpectrumData(
        source_file=Path("/tmp/test.csv"),
        columns=("wavelength", "signal"),
        rows=(
            {"wavelength": 500.0, "signal": 10.0},
            {"wavelength": float("nan"), "signal": 11.0},
            {"wavelength": 510.0, "signal": float("inf")},
            {"wavelength": 520.0, "signal": 12.0},
        ),
    )

    widget = SpectraPlot()
    assert widget.load_spectrum(spectrum) is True

    scatter_items = [
        item
        for item in widget.plot_widget.items()
        if type(item).__name__ == "ScatterPlotItem"
    ]
    assert len(scatter_items) == 1

    x_values, y_values = scatter_items[0].getData()
    assert list(x_values) == [500.0, 520.0]
    assert list(y_values) == [10.0, 12.0]


def test_failed_load_clears_previous_spectrum_state():
    """A failed load must not retain the previously loaded dataset."""

    valid_spectrum = SpectrumData(
        source_file=Path("/tmp/valid.csv"),
        columns=("wavelength", "signal"),
        rows=({"wavelength": 500.0, "signal": 10.0},),
    )
    invalid_spectrum = SpectrumData(
        source_file=Path("/tmp/invalid.csv"),
        columns=("other",),
        rows=({"other": 1.0},),
    )

    widget = SpectraPlot()
    assert widget.load_spectrum(valid_spectrum) is True

    assert widget.load_spectrum(invalid_spectrum) is False
    assert widget._current_spectrum is None
    assert widget._wavelength_column is None
    assert widget._signal_column is None

    scatter_items = [
        item
        for item in widget.plot_widget.items()
        if type(item).__name__ == "ScatterPlotItem"
    ]
    assert scatter_items == []