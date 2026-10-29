"""Auditable scientific References & Resources browser for ECAS Chunk 7."""
from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ecas.resources.catalog import (
    BENCHMARK_PLANETS,
    CATEGORY_FILTERS,
    MOLECULAR_DATABASE_SPECS,
    SCIENTIFIC_RESOURCES,
    ScientificResource,
    filter_resources,
)
from ecas.ui.source_links import source_link


def _plain_label(text: str = "") -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


class ResourcesBrowser(QWidget):
    """Browse verified scientific software, archives, molecular databases, libraries, and papers."""

    def __init__(self, parent=None, *, resources=SCIENTIFIC_RESOURCES):
        super().__init__(parent)
        self._all_resources = tuple(resources)
        self._visible_resources: tuple[ScientificResource, ...] = ()
        self._active_category = "All"

        layout = QVBoxLayout(self)
        title = _plain_label("References & Resources")
        title.setObjectName("pageTitle")
        subtitle = _plain_label(
            "Structured catalog of established scientific software, observational archives, "
            "molecular spectroscopy databases, foundational Python libraries, and benchmark "
            "publications supporting ECAS. Listing a resource records provenance and "
            "scientific context; it does not claim bundled code or unvalidated retrieval."
        )
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Category filter pill row matching the Chunk 7 specification
        filter_row = QHBoxLayout()
        self.category_buttons: dict[str, QPushButton] = {}
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        for category in CATEGORY_FILTERS:
            button = QPushButton(category)
            button.setCheckable(True)
            if category == "All":
                button.setChecked(True)
            button.clicked.connect(
                lambda checked=False, cat=category: self.set_category_filter(cat)
            )
            self._button_group.addButton(button)
            self.category_buttons[category] = button
            filter_row.addWidget(button)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Search and count bar
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Filter by title, author, DOI, molecular database, or ECAS component..."
        )
        self.search_input.textChanged.connect(self._refresh_table)
        self.count_label = _plain_label("")
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.count_label)
        layout.addLayout(search_row)

        # Resource table
        self.resource_table = QTableWidget(0, 6)
        self.resource_table.setAlternatingRowColors(True)
        self.resource_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.resource_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.resource_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.resource_table.setHorizontalHeaderLabels(
            ["Title", "Category", "Access", "Summary", "Canonical URL", "DOI"]
        )
        self.resource_table.itemSelectionChanged.connect(self._update_detail_panel)
        layout.addWidget(self.resource_table, 2)

        # Selected resource detail & action panel
        self.detail_label = _plain_label("Select a resource to inspect provenance, license, citation, and ECAS traceability.")
        layout.addWidget(self.detail_label)

        action_row = QHBoxLayout()
        self.copy_link_button = QPushButton("Copy link")
        self.copy_link_button.clicked.connect(self.copy_selected_link)
        self.copy_citation_button = QPushButton("Copy citation")
        self.copy_citation_button.clicked.connect(self.copy_selected_citation)
        self.open_link_button = QPushButton("Open link")
        self.open_link_button.clicked.connect(self.open_selected_link)
        self.copy_status = _plain_label("")
        action_row.addWidget(self.copy_link_button)
        action_row.addWidget(self.copy_citation_button)
        action_row.addWidget(self.open_link_button)
        action_row.addWidget(self.copy_status, 1)
        layout.addLayout(action_row)

        # Molecular spectroscopy applicability & benchmark target summary
        db_names = ", ".join(
            f"{spec.name} ({spec.typical_temp_range_k[0]:g}-{spec.typical_temp_range_k[1]:g} K)"
            for spec in MOLECULAR_DATABASE_SPECS
        )
        benchmark_names = ", ".join(
            f"{planet.planet_name} ({len(planet.species_assessments)} species records)"
            for planet in BENCHMARK_PLANETS
        )
        self.foundation_summary = _plain_label(
            f"Molecular database temperature regimes: {db_names}.\n"
            f"Benchmark characterization targets: {benchmark_names}."
        )
        layout.addWidget(self.foundation_summary)

        self._refresh_table()

    @property
    def active_category(self) -> str:
        return self._active_category

    @property
    def visible_resources(self) -> tuple[ScientificResource, ...]:
        return self._visible_resources

    def set_category_filter(self, category: str) -> None:
        if category not in CATEGORY_FILTERS:
            raise ValueError(f"Unsupported category filter: {category!r}")
        self._active_category = category
        button = self.category_buttons.get(category)
        if button is not None and not button.isChecked():
            button.setChecked(True)
        self._refresh_table()

    def selected_resource(self) -> ScientificResource | None:
        row = self.resource_table.currentRow()
        if 0 <= row < len(self._visible_resources):
            return self._visible_resources[row]
        return None

    def copy_selected_link(self) -> str | None:
        resource = self.selected_resource()
        if resource is None:
            self.copy_status.setText("Select a resource before copying a link.")
            return None
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(resource.canonical_url)
        self.copy_status.setText(f"Copied canonical link: {resource.canonical_url}")
        return resource.canonical_url

    def copy_selected_citation(self) -> str | None:
        resource = self.selected_resource()
        if resource is None:
            self.copy_status.setText("Select a resource before copying a citation.")
            return None
        citation_text = (
            f"{resource.citation} DOI: {resource.doi}"
            if resource.doi
            else resource.citation
        )
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(citation_text)
        self.copy_status.setText(f"Copied citation for {resource.title}.")
        return citation_text

    def open_selected_link(self) -> bool:
        resource = self.selected_resource()
        if resource is None:
            self.copy_status.setText("Select a resource before opening a link.")
            return False
        validated = source_link(resource.canonical_url)
        if not validated:
            self.copy_status.setText("Resource URL did not pass canonical HTTPS/HTTP validation.")
            return False
        opened = QDesktopServices.openUrl(QUrl(validated))
        if not opened:
            self.copy_status.setText("Could not open the resource link in an external browser.")
        return bool(opened)

    def _refresh_table(self) -> None:
        self._visible_resources = filter_resources(
            category=self._active_category,
            query=self.search_input.text(),
            resources=self._all_resources,
        )
        self.resource_table.setRowCount(len(self._visible_resources))
        for row_idx, resource in enumerate(self._visible_resources):
            values = (
                resource.title,
                resource.category,
                resource.access_label,
                resource.short_description,
                resource.canonical_url,
                resource.doi or "—",
            )
            for col_idx, text in enumerate(values):
                item = QTableWidgetItem(text)
                self.resource_table.setItem(row_idx, col_idx, item)
        self.resource_table.resizeColumnsToContents()
        self.count_label.setText(
            f"Showing {len(self._visible_resources)} of {len(self._all_resources)} resources"
        )
        if self._visible_resources:
            self.resource_table.selectRow(0)
        else:
            self._update_detail_panel()

    def _update_detail_panel(self) -> None:
        resource = self.selected_resource()
        has_selection = resource is not None
        self.copy_link_button.setEnabled(has_selection)
        self.copy_citation_button.setEnabled(has_selection)
        self.open_link_button.setEnabled(has_selection)
        if resource is None:
            self.detail_label.setText("No matching resource selected.")
            return
        doi_text = resource.doi if resource.doi else "Not assigned"
        components_text = ", ".join(resource.ecas_components)
        self.detail_label.setText(
            f"{resource.title} ({resource.category} — {resource.access_label})\n"
            f"Authors / Organization: {resource.authors_or_org} | Version / Scope: {resource.version_or_scope}\n"
            f"Canonical URL: {resource.canonical_url} | DOI: {doi_text} | License: {resource.license_spdx}\n"
            f"Citation: {resource.citation}\n"
            f"ECAS Contribution: {resource.ecas_contribution}\n"
            f"Traceable ECAS Components: {components_text}"
        )

