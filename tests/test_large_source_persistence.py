"""Tests for large-source external project persistence (v2 content-addressed storage)."""
from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import pytest

from ecas import persistence
from ecas.ingestion.tabular_formats import import_fits_bintable_spectrum
from ecas.models.spectrum import SpectrumData
from ecas.projects import ProjectStore, MAX_INLINE_SOURCE_BYTES
from tests.test_fits_streaming import primary, table_header, table_data, measured_rows


def create_large_fits_spectrum(path: Path, image_mb: int = 20) -> tuple[Path, SpectrumData]:
    """Create a valid FITS file larger than 16 MiB containing real-derived spectral rows."""
    image_size = image_mb * 1024 * 1024
    padded = (image_size + 2879) // 2880 * 2880
    with path.open("wb") as stream:
        stream.write(primary(image_size))
        stream.seek(padded - 1, 1)
        stream.write(b"\0")
        stream.write(table_header())
        stream.write(table_data())
    assert path.stat().st_size > 16 * 1024 * 1024
    spectrum = import_fits_bintable_spectrum(path)
    return path, spectrum


def test_large_source_persists_externally_without_database_inflation(tmp_path: Path):
    """Verify that >16 MiB files are stored in project sources/ and keep SQLite rows tiny."""
    fits_path, spectrum = create_large_fits_spectrum(tmp_path / "large_input.fits", image_mb=20)
    original_size = fits_path.stat().st_size
    with fits_path.open("rb") as f:
        hasher = sha256()
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
        expected_hash = hasher.hexdigest()

    store = ProjectStore(tmp_path / "projects")
    store.create("astronomy")

    # Attach large source
    record_id = store.attach("astronomy", spectrum)
    assert record_id > 0

    # 1. Inspect SQLite row size directly: must NOT contain 26+ MiB of base64!
    db_path = store.root / "astronomy/data.sqlite"
    with closing(sqlite3.connect(db_path)) as conn:
        row = conn.execute("SELECT data FROM spectra WHERE id = ?", (record_id,)).fetchone()
        assert row is not None
        raw_json_str = row[0]
        # The SQLite row text should be tiny (typically < 10 KB), NOT inflated by 20+ MiB!
        assert len(raw_json_str.encode("utf-8")) < 25_000

        data = json.loads(raw_json_str)
        attachment = data["attachment"]
        assert attachment["schema"] == "ecas-project-source-v2"
        assert attachment["source_sha256"] == expected_hash
        assert attachment["source_size_bytes"] == original_size
        assert "source_bytes" not in attachment  # No bloated inline base64
        assert "sources/" in attachment["source_relpath"]

    # 2. Verify external file on disk
    external_file = store.root / "astronomy" / attachment["source_relpath"]
    assert external_file.is_file()
    assert external_file.stat().st_size == original_size

    # 3. Delete original input file to verify project self-containment
    fits_path.unlink()

    # 4. Reopen from project store
    reopened_store = ProjectStore(store.root)
    spectra_list = reopened_store.spectra("astronomy")
    assert len(spectra_list) == 1
    reopened = spectra_list[0]
    assert reopened.record_id == record_id
    assert reopened.spectrum == spectrum
    assert reopened.source_path == external_file

    # Streamed verification of bytes
    reopened_bytes = reopened.source_bytes()
    assert len(reopened_bytes) == original_size
    assert sha256(reopened_bytes).hexdigest() == expected_hash


def test_large_source_detects_disk_tampering(tmp_path: Path):
    """Verify that any modification to the external source file is detected."""
    fits_path, spectrum = create_large_fits_spectrum(tmp_path / "large_input.fits", image_mb=18)
    store = ProjectStore(tmp_path / "projects")
    store.create("secure_proj")
    store.attach("secure_proj", spectrum)

    item = store.spectra("secure_proj")[0]
    source_file = item.source_path
    assert source_file is not None and source_file.is_file()

    # Tamper with 1 byte in the external file
    with source_file.open("r+b") as f:
        f.seek(100)
        orig_byte = f.read(1)
        f.seek(100)
        f.write(b"\xFF" if orig_byte != b"\xFF" else b"\x00")

    with pytest.raises(persistence.PersistenceError, match="Saved source failed integrity validation"):
        store.spectra("secure_proj")


def test_copy_v2_attachment_to_another_project(tmp_path: Path):
    """Verify copying a v2 external attachment across projects copies the external source file."""
    fits_path, spectrum = create_large_fits_spectrum(tmp_path / "large_input.fits", image_mb=17)
    store = ProjectStore(tmp_path / "projects")
    store.create("project_a")
    store.attach("project_a", spectrum)

    # Load from project A
    item_a = store.spectra("project_a")[0]
    assert item_a.attachment["schema"] == "ecas-project-source-v2"
    file_a = item_a.source_path
    assert file_a.is_file()

    # Copy to project B
    store.create("project_b")
    store.attach("project_b", item_a.spectrum, existing_attachment=item_a.attachment)

    item_b = store.spectra("project_b")[0]
    file_b = item_b.source_path
    assert file_b is not None and file_b.is_file()
    assert file_b != file_a  # Independent copies in each project directory
    assert file_b.stat().st_size == file_a.stat().st_size

    # Remove project A completely: project B remains intact and self-contained
    import shutil
    shutil.rmtree(store.root / "project_a")

    reopened_b = store.spectra("project_b")[0]
    assert reopened_b.spectrum == spectrum
    assert reopened_b.source_path.is_file()


def test_failed_database_insert_removes_copied_external_file(tmp_path: Path):
    """Verify that no orphan file remains in sources/ if database insert aborts."""
    fits_path, spectrum = create_large_fits_spectrum(tmp_path / "large_input.fits", image_mb=18)
    store = ProjectStore(tmp_path / "projects")
    store.create("abort_proj")

    # Install trigger that aborts insertion
    db_path = store.root / "abort_proj/data.sqlite"
    with closing(sqlite3.connect(db_path)) as conn:
        with conn:
            conn.execute(
                "CREATE TRIGGER fail_insert BEFORE INSERT ON spectra BEGIN "
                "SELECT RAISE(ABORT, 'synthetic abort'); END"
            )

    with pytest.raises(persistence.PersistenceError):
        store.attach("abort_proj", spectrum)

    # Check sources/ folder: must have 0 files
    sources_dir = store.root / "abort_proj/sources"
    if sources_dir.exists():
        assert list(sources_dir.iterdir()) == []

