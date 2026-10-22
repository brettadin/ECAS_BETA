"""Persistence layer for ECAS spectrum data.

This module provides storage and retrieval of SpectrumData objects using SQLite,
storing each spectrum as a separate JSON document.

Storage scheme:
    projects/<project_id>/data.sqlite

Each row in the database stores one spectrum's complete SpectrumData as JSON.
"""

import json
import re
import sqlite3
from pathlib import Path
from typing import Optional, List
from ecas.models.spectrum import SpectrumData


# Project ID validation pattern - alphanumeric + underscore/hyphen only
PROJECT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")


class PersistenceError(Exception):
    """Base exception for persistence layer errors."""

    pass


class InvalidProjectIdError(PersistenceError):
    """Raised when a project ID is invalid."""

    pass


class DatabaseNotFoundError(PersistenceError):
    """Raised when the expected database file is missing."""

    pass


def validate_project_id(project_id: str, base_path: Path) -> Path:
    """Validate a project ID and ensure its path stays within base_path.

    Raises:
        InvalidProjectIdError: If the ID is invalid or the resolved path
            escapes the approved projects directory.
    """
    if not isinstance(project_id, str) or not project_id:
        raise InvalidProjectIdError("Project ID must be a non-empty string.")

    if not PROJECT_ID_PATTERN.fullmatch(project_id):
        raise InvalidProjectIdError(
            "Project ID may contain only letters, numbers, underscores, "
            "and hyphens, and must begin with a letter or number."
        )

    try:
        resolved_base = Path(base_path).resolve()
        project_path = (resolved_base / project_id).resolve()

        if not project_path.is_relative_to(resolved_base):
            raise InvalidProjectIdError(
                "Project path must remain inside the projects directory."
            )

        return project_path

    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise InvalidProjectIdError(
            f"Could not validate project path: {exc}"
        ) from exc


def get_project_database(project_id: str, projects_dir: Path) -> Path:
    """Get the path to a project's SQLite database.

    Args:
        project_id: Validated project identifier
        projects_dir: Base directory for all projects

    Returns:
        Absolute path to the project's data.sqlite file

    Raises:
        InvalidProjectIdError: If project_id is invalid
    """
    validated_path = validate_project_id(project_id, projects_dir)
    database_path = validated_path / "data.sqlite"
    return database_path


def _get_connection(database_path: Path, create_if_missing: bool = True) -> sqlite3.Connection:
    """Get a SQLite connection to the project's database.

    Args:
        database_path: Absolute path to the SQLite database file
        create_if_missing: Whether to create the database if it doesn't exist

    Returns:
        An open SQLite3 connection object
    """
    # Ensure the directory exists
    database_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(database_path))
    return conn


def _initialize_schema(conn: sqlite3.Connection) -> None:
    """Create or initialize the spectrum storage schema.

    Args:
        conn: Open SQLite connection
    """
    # Create schema if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS spectra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL,
            data JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create index for faster project-based queries
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_spectra_project_id ON spectra(project_id)
    """)


def _to_spectrums_dict(data_dict: dict) -> SpectrumData:
    """Deserialize a dictionary back to SpectrumData."""
    warnings = data_dict.get("warnings", ())
    if not isinstance(warnings, tuple):
        warnings = tuple(warnings) if warnings else ()

    return SpectrumData(
        source_file=Path(data_dict["source_file"]),
        rows=tuple(data_dict["rows"]),
        columns=tuple(data_dict["columns"]),
        axis_unit=data_dict.get("axis_unit"),
        signal_unit=data_dict.get("signal_unit"),
        signal_type=data_dict.get("signal_type"),
        warnings=warnings,
    )


def save_spectrum_to_database(
    spectrum: SpectrumData,

    project_id: str,
    projects_dir: Path,
    database_if_exists: Optional[sqlite3.Connection] = None
) -> int:
    """Save a spectrum to its project's SQLite database.

    Args:
        spectrum: The SpectrumData object to persist
        project_id: Validated project identifier
        projects_dir: Base directory for all projects
        database_if_exists: Optional existing connection (for performance)

    Returns:
        The auto-incremented primary key of the inserted row

    Raises:
        PersistenceError: If saving fails
        InvalidProjectIdError: If project_id is invalid
    """
    database_path = get_project_database(project_id, projects_dir)

    if database_if_exists is None:
        conn = _get_connection(database_path, create_if_missing=True)
        try:
            # Initialize schema on first write to this database
            _initialize_schema(conn)

            # Serialize SpectrumData to JSON
            data_json = json.dumps({
                "source_file": str(spectrum.source_file),
                "rows": spectrum.rows,
                "columns": spectrum.columns,
                "axis_unit": spectrum.axis_unit,
                "signal_unit": spectrum.signal_unit,
                "signal_type": spectrum.signal_type,
                "warnings": spectrum.warnings,
            })

            # Insert the spectrum as JSON
            cursor = conn.execute(
                """INSERT INTO spectra (project_id, data) VALUES (?, ?)""",
                (project_id, data_json),
            )
            conn.commit()

            return cursor.lastrowid


        finally:
            conn.close()

    else:
        # Use provided connection
        _initialize_schema(database_if_exists)
        data_json = json.dumps({
            "source_file": str(spectrum.source_file),
            "rows": spectrum.rows,
            "columns": spectrum.columns,
            "axis_unit": spectrum.axis_unit,
            "signal_unit": spectrum.signal_unit,
            "signal_type": spectrum.signal_type,
            "warnings": spectrum.warnings,
        })
        cursor = database_if_exists.execute(
            """INSERT INTO spectra (project_id, data) VALUES (?, ?)""",
            (project_id, data_json),
        )
        database_if_exists.commit()

        return cursor.lastrowid


def load_spectra_from_database(project_id: str, projects_dir: Path) -> List[SpectrumData]:
    """Load all spectra from a project's SQLite database.

    Args:
        project_id: Validated project identifier
        projects_dir: Base directory for all projects

    Returns:
        List of SpectrumData objects for this project

    Raises:
        PersistenceError: If loading fails
        InvalidProjectIdError: If project_id is invalid
    """
    database_path = get_project_database(project_id, projects_dir)

    # Check if database exists
    if not database_path.exists():
        return []

    conn = _get_connection(database_path, create_if_missing=False)
    try:
        # Load all spectra for this project
        cursor = conn.execute(
            """SELECT data FROM spectra WHERE project_id = ?""",
            (project_id,)
        )

        spectra = []
        for row in cursor.fetchall():
            data_dict = json.loads(row[0])
            spectrum_dict: dict = data_dict

            spectrum = _to_spectrums_dict(spectrum_dict)
            spectra.append(spectrum)

        return spectra

    finally:
        conn.close()


def load_spectrum_by_index(project_id: str, projects_dir: Path, index: int) -> Optional[SpectrumData]:
    """Load a specific spectrum from a project's database by zero-based index.

    Args:
        project_id: Validated project identifier
        projects_dir: Base directory for all projects
        index: Zero-based index of the spectrum to load (0 = first spectrum in DB)

    Returns:
        The SpectrumData object at the specified index, or None if not found/empty
    """
    spectra = load_spectra_from_database(project_id, projects_dir)
    if 0 <= index < len(spectra):
        return spectra[index]
    return None


def clear_project_database(project_id: str, projects_dir: Path) -> None:
    """Clear all spectra from a project's database.

    WARNING: This deletes all data for the project!

    Args:
        project_id: Validated project identifier
        projects_dir: Base directory for all projects
    """
    database_path = get_project_database(project_id, projects_dir)

    if not database_path.exists():
        raise DatabaseNotFoundError(f"No database exists for project '{project_id}'")

    conn = _get_connection(database_path, create_if_missing=True)
    try:
        # Drop all data but keep schema
        conn.execute("DELETE FROM spectra")
        conn.commit()
    finally:
        conn.close()


def count_spectra(project_id: str, projects_dir: Path) -> int:
    """Count the number of spectra stored for a project.

    Args:
        project_id: Validated project identifier
        projects_dir: Base directory for all projects

    Returns:
        Number of spectra in the project's database (0 if no database exists)
    """
    database_path = get_project_database(project_id, projects_dir)

    if not database_path.exists():
        return 0

    conn = _get_connection(database_path, create_if_missing=False)
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM spectra")
        count = cursor.fetchone()[0]
        return count
    finally:
        conn.close()
