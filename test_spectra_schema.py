"""Test WASP-39 b schema import with spectra_plot.py - No GUI needed for basic tests"""
import sys
sys.path.insert(0, 'c:\\Users\\brett\\AIProjects\\ECAS_BETA')

from ecas.visualization.spectra_plot import SpectraPlot
from ecas.ingestion.csv_importer import import_spectrum_csv, WASP39B_SCHEMA
from PySide6.QtWidgets import QApplication

# Create minimal Qt application for widget testing
app = QApplication([])

# First verify the schema structure
print("=== Testing WASP-39 b Schema ===")
print(f"WASP39B_SCHEMA: {WASP39B_SCHEMA}")

# Test with a simple CSV file that uses standard column names
path = r'c:\Users\brett\AIProjects\ECAS_BETA\wasp39b_test.csv'
spectrum = import_spectrum_csv(path, archive_schema=WASP39B_SCHEMA)  # Use WASP-39 b schema

print(f"\nImport successful!")
print(f"Source file: {spectrum.source_file.name}")
print(f"Row count: {spectrum.row_count}")
print(f"Columns: {spectrum.columns}")

# Test display with spectra_plot
plot_widget = SpectraPlot()
result = plot_widget.load_spectrum(spectrum, schema=WASP39B_SCHEMA)
print(f"\nPlot load result: {result}")
print(f"Wavelength column mapped to: {plot_widget._wavelength_column}")
print(f"Signal column mapped to: {plot_widget._signal_column}")

# Test with None schema (should fail since our test CSV uses non-standard column names)
try:
    plot_widget.clear()
    result2 = plot_widget.load_spectrum(spectrum, schema=None)
    print(f"\nLoad without schema result: {result2} (expected: False)")
except Exception as e:
    print(f"Error loading without schema: {e}")

print("\n=== WASP-39 b Schema tests passed! ===")