"""Project selection and saved-spectrum actions; persistence lives in services."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QListWidget


class ProjectBrowser(QWidget):
    saveRequested = Signal(str)
    spectrumReady = Signal(object)

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.records = []
        self.has_spectrum = False
        layout = QVBoxLayout(self)
        title = QLabel('Projects')
        title.setObjectName('pageTitle')
        layout.addWidget(title)
        self.description = QLabel('Create or select a project, then add the spectrum currently displayed in Spectral Data. Saved sources and provenance reopen offline.')
        self.description.setWordWrap(True)
        layout.addWidget(self.description)
        create_row = QHBoxLayout()
        self.name = QLineEdit()
        self.name.setPlaceholderText('Project ID: letters, numbers, underscores or hyphens')
        self.create_button = QPushButton('Create project')
        create_row.addWidget(self.name)
        create_row.addWidget(self.create_button)
        layout.addLayout(create_row)
        select_row = QHBoxLayout()
        self.projects = QComboBox()
        self.refresh_button = QPushButton('Refresh projects')
        select_row.addWidget(self.projects, 1)
        select_row.addWidget(self.refresh_button)
        layout.addLayout(select_row)
        self.save_button = QPushButton('Add displayed spectrum to project')
        layout.addWidget(self.save_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.status = QLabel('No project selected.')
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.spectra = QListWidget()
        layout.addWidget(self.spectra)
        self.open_button = QPushButton('Open selected spectrum')
        layout.addWidget(self.open_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.create_button.clicked.connect(self.create_project)
        self.refresh_button.clicked.connect(self.refresh)
        self.projects.currentTextChanged.connect(self.reload)
        self.spectra.currentRowChanged.connect(lambda _: self._buttons())
        self.save_button.clicked.connect(lambda: self.saveRequested.emit(self.projects.currentText()))
        self.open_button.clicked.connect(self.open_selected)
        self.refresh()

    def _buttons(self):
        self.save_button.setEnabled(self.has_spectrum and bool(self.projects.currentText()))
        self.open_button.setEnabled(0 <= self.spectra.currentRow() < len(self.records))

    def set_spectrum_available(self, available):
        self.has_spectrum = available
        self._buttons()

    def fail(self, error):
        self.status.setText(f'Project operation failed: {error}')
        self._buttons()

    def refresh(self, selected=None):
        selected = selected or self.projects.currentText()
        try:
            names = self.store.projects()
            self.projects.blockSignals(True)
            self.projects.clear()
            self.projects.addItems(names)
            if selected in names:
                self.projects.setCurrentText(selected)
        except Exception as error:
            self.projects.blockSignals(True)
            self.projects.clear()
            self.records = []
            self.spectra.clear()
            self.fail(error)
            return
        finally:
            self.projects.blockSignals(False)
        self.reload()

    def create_project(self):
        try:
            name = self.name.text().strip()
            self.store.create(name)
            self.refresh(name)
            self.name.clear()
        except Exception as error:
            self.fail(error)

    def reload(self, *_):
        self.records = []
        self.spectra.clear()
        name = self.projects.currentText()
        try:
            if name:
                self.records = self.store.spectra(name)
                for record in self.records:
                    integrity = 'source preserved' if record.attachment else 'legacy: no source attachment'
                    self.spectra.addItem(f'{record.record_id}: {record.spectrum.source_file.name} | {record.spectrum.row_count} rows | {integrity}')
                self.status.setText(f'{name}: {len(self.records)} saved spectra. Storage: {self.store.root}')
            else:
                self.status.setText('Create a project to get started.')
        except Exception as error:
            self.fail(error)
        self._buttons()

    def open_selected(self):
        index = self.spectra.currentRow()
        if not 0 <= index < len(self.records):
            return
        identifier = self.records[index].record_id
        try:
            # Revalidate when opening, not just when the list was populated.
            current = self.store.spectra(self.projects.currentText())
            record = next((item for item in current if item.record_id == identifier), None)
            if record is None:
                raise ValueError('Record no longer exists; refresh the project spectra.')
            self.spectrumReady.emit(record)
        except Exception as error:
            self.fail(error)
