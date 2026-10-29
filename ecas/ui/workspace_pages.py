"""Workspace guidance and existing session preferences, without storage side effects."""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QPushButton, QLineEdit, QComboBox,
)


def _text(value):
    label = QLabel(value)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


class OverviewPage(QWidget):
    """Describe the workflow and summarize already loaded state on page entry."""

    def __init__(self, state_getter, navigate, parent=None):
        super().__init__(parent)
        self.state_getter = state_getter
        layout = QVBoxLayout(self)
        title = _text('ECAS workspace')
        title.setObjectName('pageTitle')
        layout.addWidget(title)
        layout.addWidget(_text(
            'Import an observation, save it in a research project, retrieve a molecular '
            'reference, then inspect the inputs separately in Comparisons.'))
        self.status = _text('No datasets loaded.')
        layout.addWidget(self.status)
        self.shortcuts = {}
        steps = (
            (2, 'Inspect an observation', 'Import CSV files or search the NASA archive for supported transmission tables.'),
            (1, 'Open research projects', 'Save observations with their available source provenance and reopen saved records offline.'),
            (3, 'Find molecular references', 'Search ExoMol; retrieve supported CO2, H2O or CH4 cross sections, or reopen cached products.'),
            (4, 'Inspect selected inputs', 'Add observation snapshots and independently select cached references. Choices last for this session.'),
            (5, 'View settings and data locations', 'Check storage paths and choose how local CSV files are interpreted.'),
            (6, 'Browse references and resources', 'Inspect canonical scientific software, archives, molecular databases, libraries, and benchmark publications.'),
        )
        for index, caption, description in steps:
            button = QPushButton(caption)
            button.clicked.connect(lambda checked=False, page=index: navigate(page))
            self.shortcuts[index] = button
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(_text(description))
        layout.addWidget(_text(
            'Calculated cross sections are reference products, not transit-depth predictions '
            'or molecular detections. Comparison calculations and atmospheric modelling '
            'are not available. Successful retrieval does not establish scientific compatibility.'))
        layout.addStretch()

    def refresh(self):
        # The caller supplies strings from existing in-memory state only.
        self.status.setText(self.state_getter())


class SettingsPage(QWidget):
    """Mirror the existing CSV choice and expose configured locations read-only."""

    def __init__(self, schema_selector, locations, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = _text('Settings')
        title.setObjectName('pageTitle')
        layout.addWidget(title)
        layout.addWidget(_text(
            'CSV interpretation applies to the next CSV import from either import entry '
            'point. It does not change already loaded or saved spectra, and does not '
            'affect NASA .tbl imports. This choice lasts for the current session.'))
        form = QFormLayout()
        self.csv_schema = QComboBox()
        self.csv_schema.addItems([schema_selector.itemText(i) for i in range(schema_selector.count())])
        self.csv_schema.setCurrentIndex(schema_selector.currentIndex())
        self.csv_schema.currentIndexChanged.connect(schema_selector.setCurrentIndex)
        schema_selector.currentIndexChanged.connect(self.csv_schema.setCurrentIndex)
        form.addRow('CSV schema:', self.csv_schema)
        layout.addLayout(form)
        layout.addWidget(_text(
            'Active data locations (read-only). Select a path to copy it. '
            'This page does not move, delete or scan stored data.'))
        paths = QFormLayout()
        self.location_fields = {}
        for name, path in locations.items():
            field = QLineEdit(str(Path(path).absolute()))
            field.setReadOnly(True)
            field.setToolTip(field.text())
            self.location_fields[name] = field
            paths.addRow(name + ':', field)
        layout.addLayout(paths)
        layout.addWidget(_text(
            'Projects retain saved observations and available source provenance. '
            'NASA and ExoMol caches retain downloaded products for offline reopening. '
            'Observation choices in Comparisons are held in memory and are lost when '
            'the application closes; save observations in Projects for later use.'))
        layout.addWidget(_text(
            'Online access: explicit search, refresh and download actions use the supported '
            'public archive services without an account. Offline reopening needs no new '
            'request. Page changes preserve active requests; use the browser cancellation '
            'controls to stop a pending request.'))
        layout.addStretch()
