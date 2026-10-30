"""Project attachment use cases; SQL stays in persistence and UI stays separate.

Supports both v1 (inline base64 for small sources <=16 MiB) and v2 (external
content-addressed streamed storage in <project_dir>/sources/ for large containers
up to 8 GiB), preserving full provenance, SHA-256 integrity, and reproducibility.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any

from ecas import persistence
from ecas.comparison.persistence import load_comparison_records, save_comparison_record
from ecas.ingestion.import_manager import import_spectrum
from ecas.ingestion.nasa_archive import read_cached
from ecas.ingestion.nasa_table import TransmissionTable, import_transmission_table
from ecas.models.spectrum import SpectrumData
from ecas.observations import hash_source_file

# Limits
MAX_SOURCE_BYTES = 16 * 1024 * 1024  # Legacy alias preserved for backwards compatibility / tests
MAX_INLINE_SOURCE_BYTES = 16 * 1024 * 1024  # 16 MiB inline base64 limit
MAX_EXTERNAL_SOURCE_BYTES = 8 * 1024 * 1024 * 1024  # 8 GiB external container limit


def _safe_filename(name: str) -> str:
    """Sanitize a filename for secure filesystem storage."""
    cleaned = "".join(c if c.isalnum() or c in "._- " else "_" for c in name).strip()
    return cleaned or "source.bin"


def stream_copy_and_hash(src_path: Path, dst_path: Path) -> tuple[str, int]:
    """Stream-copy a source file to destination in 1 MiB chunks while computing SHA-256."""
    hasher = sha256()
    total_bytes = 0
    with src_path.open("rb") as src, dst_path.open("wb") as dst:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            hasher.update(chunk)
            dst.write(chunk)
            total_bytes += len(chunk)
    return hasher.hexdigest(), total_bytes


def _source_bytes(source: Path) -> bytes:
    """Read bounded source bytes for inline v1 storage."""
    with source.open("rb") as stream:
        raw = stream.read(MAX_SOURCE_BYTES + 1)
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError("Project source exceeds 16 MiB limit")
    return raw


def _payload(spectrum: SpectrumData) -> dict[str, Any]:
    return dict(
        source_file=str(spectrum.source_file),
        rows=spectrum.rows,
        columns=spectrum.columns,
        axis_unit=spectrum.axis_unit,
        signal_unit=spectrum.signal_unit,
        signal_type=spectrum.signal_type,
        warnings=spectrum.warnings,
        **({"metadata": spectrum.metadata} if spectrum.metadata else {}),
    )


def _digest(spectrum: SpectrumData, attachment: dict, *, source_file: str | None = None) -> str:
    payload = _payload(spectrum)
    if source_file is not None:
        payload["source_file"] = source_file
    return sha256(
        json.dumps(
            dict(spectrum=payload, attachment=attachment),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def _verified(
    spectrum: SpectrumData,
    attachment: dict,
    *,
    project_dir: Path | None = None,
    source_file: str | None = None,
) -> dict:
    if not isinstance(attachment, dict):
        raise ValueError("Unsupported project source record")
    schema = attachment.get("schema")
    if schema not in ("ecas-project-source-v1", "ecas-project-source-v2"):
        raise ValueError("Unsupported project source record")

    unsigned = {key: value for key, value in attachment.items() if key != "integrity_sha256"}
    if _digest(spectrum, unsigned, source_file=source_file) != attachment.get("integrity_sha256"):
        raise ValueError("Saved spectrum or provenance changed")

    if schema == "ecas-project-source-v1":
        raw = base64.b64decode(attachment["source_bytes"], validate=True)
        if len(raw) > MAX_SOURCE_BYTES or sha256(raw).hexdigest() != attachment["source_sha256"]:
            raise ValueError("Saved source failed integrity validation")
    elif schema == "ecas-project-source-v2":
        if project_dir is not None:
            rel = attachment.get("source_relpath", "")
            if not rel or ".." in rel or Path(rel).is_absolute():
                raise ValueError("Invalid source relative path in project attachment")
            target = (project_dir / rel).resolve()
            if not target.is_file() or not target.is_relative_to(project_dir.resolve()):
                raise ValueError("External source file missing or outside project")
            if target.stat().st_size != attachment.get("source_size_bytes"):
                raise ValueError("External source file size changed")
            if hash_source_file(target) != attachment.get("source_sha256"):
                raise ValueError("Saved source failed integrity validation")

    # v1/v2 hashes include the original path spelling. Verify that exact persisted
    # spelling before adapting the envelope to this platform's Path rendering.
    if source_file is not None and source_file != str(spectrum.source_file):
        return dict(unsigned, integrity_sha256=_digest(spectrum, unsigned))
    return attachment


@dataclass(frozen=True)
class ProjectSpectrum:
    record_id: int
    spectrum: SpectrumData
    attachment: dict | None
    project_dir: Path | None = None

    @property
    def details(self) -> TransmissionTable | None:
        if self.attachment is None or "table_metadata" not in self.attachment.get("provenance", {}):
            return None
        data = self.attachment["provenance"]
        return TransmissionTable(
            self.spectrum,
            tuple(map(tuple, data["table_metadata"])),
            tuple(map(tuple, data["column_units"])),
            self.attachment["source_sha256"],
        )

    @property
    def import_schema(self) -> dict | None:
        return self.attachment["provenance"].get("import_schema") if self.attachment else None

    @property
    def source_path(self) -> Path | None:
        """Return the verified local source path if stored externally (v2), or None if inline (v1)."""
        if (
            self.attachment
            and self.attachment.get("schema") == "ecas-project-source-v2"
            and self.project_dir
        ):
            return self.project_dir / self.attachment["source_relpath"]
        return None

    def source_bytes(self) -> bytes:
        """Return the raw bytes of the attached source file (v1 or v2)."""
        if self.attachment is None:
            raise ValueError("No attachment associated with this spectrum")
        schema = self.attachment.get("schema")
        if schema == "ecas-project-source-v1":
            return base64.b64decode(self.attachment["source_bytes"], validate=True)
        if schema == "ecas-project-source-v2":
            path = self.source_path
            if path is None or not path.is_file():
                raise ValueError("External source file not found")
            return path.read_bytes()
        raise ValueError(f"Unsupported attachment schema: {schema}")


def get_attachment_bytes(attachment: dict, project_dir: Path | None = None) -> bytes:
    """Retrieve raw bytes of an attachment regardless of v1 (inline) or v2 (external) storage."""
    schema = attachment.get("schema")
    if schema == "ecas-project-source-v1":
        return base64.b64decode(attachment["source_bytes"], validate=True)
    if schema == "ecas-project-source-v2":
        if project_dir is None:
            raise ValueError("project_dir is required to read v2 external attachment bytes")
        rel = attachment.get("source_relpath", "")
        path = project_dir / rel
        return path.read_bytes()
    raise ValueError(f"Unsupported attachment schema: {schema}")


def get_attachment_path(attachment: dict, project_dir: Path) -> Path | None:
    """Return local path to the source file if stored externally (v2), or None if inline (v1)."""
    if attachment.get("schema") == "ecas-project-source-v2":
        rel = attachment.get("source_relpath", "")
        return project_dir / rel
    return None


class ProjectStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        if self.root.is_symlink() or self.root.is_junction():
            raise persistence.PersistenceError("Linked project roots are unsupported")

    def projects(self) -> list[str]:
        return persistence.list_project_ids(self.root)

    def create(self, name: str) -> None:
        persistence.create_project(name, self.root)

    def attach(
        self,
        name: str,
        spectrum: SpectrumData,
        schema: dict | None = None,
        existing_attachment: dict | None = None,
        *,
        expected_source_sha256: str | None = None,
        use_external: bool = False,
    ) -> int:
        """Snapshot a validated local source, or copy a verified saved attachment.

        The original path remains origin metadata. Reopening uses saved values and
        source bytes/external content-addressed files, so neither the cache nor the
        original external path is a dependency.
        """
        copied_file: Path | None = None
        try:
            database = persistence._checked_project_database(name, self.root)
            if not database.is_file():
                raise ValueError("Create or select an existing project first")

            project_dir = self.root / name

            if existing_attachment is not None:
                schema_name = existing_attachment.get("schema")
                if schema_name == "ecas-project-source-v1":
                    attachment = _verified(spectrum, existing_attachment, project_dir=project_dir)
                elif schema_name == "ecas-project-source-v2":
                    rel = existing_attachment["source_relpath"]
                    dst_file = project_dir / rel
                    if not dst_file.is_file():
                        # Locate the source file in another project in self.root or original path
                        found = False
                        for p in self.projects():
                            candidate = self.root / p / rel
                            if candidate.is_file() and hash_source_file(candidate) == existing_attachment["source_sha256"]:
                                dst_file.parent.mkdir(parents=True, exist_ok=True)
                                stream_copy_and_hash(candidate, dst_file)
                                copied_file = dst_file
                                found = True
                                break
                        if not found and spectrum.source_file.is_file() and hash_source_file(spectrum.source_file) == existing_attachment["source_sha256"]:
                            dst_file.parent.mkdir(parents=True, exist_ok=True)
                            stream_copy_and_hash(spectrum.source_file, dst_file)
                            copied_file = dst_file
                            found = True
                        if not found:
                            raise ValueError("Cannot copy attachment: external source file not found")
                    attachment = _verified(spectrum, existing_attachment, project_dir=project_dir)
                else:
                    raise ValueError("Unsupported project source record")
            else:
                source = Path(spectrum.source_file)
                if not source.is_file():
                    raise ValueError(f"Source file not found: {source}")
                source_size = source.stat().st_size
                if source_size > MAX_EXTERNAL_SOURCE_BYTES:
                    raise ValueError(f"Project source exceeds {MAX_EXTERNAL_SOURCE_BYTES // (1024**3)} GiB limit")

                # If size > MAX_INLINE_SOURCE_BYTES or explicitly requested, use v2 external storage
                is_external = use_external or (source_size > MAX_INLINE_SOURCE_BYTES)

                if is_external:
                    sources_dir = project_dir / "sources"
                    sources_dir.mkdir(parents=True, exist_ok=True)
                    safe_name = _safe_filename(source.name)

                    # Stream-copy to temp file first to verify hash
                    temp_dst = sources_dir / f"tmp_{source.name}"
                    source_hash, bytes_copied = stream_copy_and_hash(source, temp_dst)
                    if expected_source_sha256 is not None and source_hash != expected_source_sha256:
                        temp_dst.unlink(missing_ok=True)
                        raise ValueError("Source changed since import; reimport it before attaching")

                    final_name = f"{source_hash}_{safe_name}"
                    final_dst = sources_dir / final_name
                    if final_dst.exists():
                        temp_dst.unlink(missing_ok=True)
                    else:
                        temp_dst.replace(final_dst)
                    copied_file = final_dst

                    provenance = dict(original_path=str(source), import_schema=schema)
                    parsed = import_spectrum(source, archive_schema=schema)
                    if parsed != spectrum:
                        raise ValueError("Source no longer matches the displayed spectrum; reimport it first")
                    if hash_source_file(source) != source_hash:
                        raise ValueError("Source changed while attaching")

                    attachment = dict(
                        schema="ecas-project-source-v2",
                        source_name=source.name,
                        source_sha256=source_hash,
                        source_size_bytes=bytes_copied,
                        source_relpath=f"sources/{final_name}",
                        provenance=provenance,
                    )
                    attachment["integrity_sha256"] = _digest(spectrum, attachment)
                else:
                    raw = _source_bytes(source)
                    if expected_source_sha256 is not None and sha256(raw).hexdigest() != expected_source_sha256:
                        raise ValueError("Source changed since import; reimport it before attaching")
                    provenance = dict(original_path=str(source), import_schema=schema)
                    if source.suffix.lower() == ".tbl":
                        details = import_transmission_table(source)
                        parsed = details.spectrum
                        if sha256(raw).hexdigest() != details.source_sha256:
                            raise ValueError("Source changed while attaching")
                        provenance.update(
                            import_schema=None,
                            table_metadata=details.metadata,
                            column_units=details.column_units,
                        )
                        if source.name == "source.tbl" and (source.parent / "record.json").exists():
                            record, _ = read_cached(source.parent)
                            metadata = (source.parent / "metadata.json").read_bytes()
                            if (
                                record["sha256"] != details.source_sha256
                                or sha256(metadata).hexdigest() != record["metadata_sha256"]
                            ):
                                raise ValueError("Cache provenance changed while attaching")
                            provenance.update(
                                cache_record=record,
                                metadata_bytes=base64.b64encode(metadata).decode("ascii"),
                            )
                    else:
                        parsed = import_spectrum(source, archive_schema=schema)
                        if _source_bytes(source) != raw:
                            raise ValueError("Source changed while attaching")
                    if parsed != spectrum:
                        raise ValueError("Source no longer matches the displayed spectrum; reimport it first")
                    attachment = dict(
                        schema="ecas-project-source-v1",
                        source_name=source.name,
                        source_sha256=sha256(raw).hexdigest(),
                        source_bytes=base64.b64encode(raw).decode("ascii"),
                        provenance=provenance,
                    )
                    attachment["integrity_sha256"] = _digest(spectrum, attachment)

            size = len(
                json.dumps(
                    dict(_payload(spectrum), attachment=attachment),
                    allow_nan=False,
                ).encode()
            )
            if size > 64 * 1024 * 1024:
                raise ValueError("Project spectrum exceeds 64 MiB record limit")

            return persistence.save_spectrum_to_database(
                spectrum, name, self.root, attachment=attachment
            )

        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
            if copied_file is not None and copied_file.is_file():
                try:
                    copied_file.unlink(missing_ok=True)
                except OSError:
                    pass
            raise persistence.PersistenceError(f"Could not attach spectrum: {error}") from error

    def spectra(self, name: str) -> list[ProjectSpectrum]:
        try:
            result = []
            project_dir = self.root / name
            for identifier, data in persistence.load_spectrum_records(name, self.root):
                spectrum = persistence._to_spectrums_dict(data)
                attachment = (
                    _verified(
                        spectrum,
                        data["attachment"],
                        project_dir=project_dir,
                        source_file=data["source_file"],
                    )
                    if "attachment" in data
                    else None
                )
                result.append(
                    ProjectSpectrum(
                        identifier,
                        spectrum,
                        attachment,
                        project_dir=project_dir,
                    )
                )
            return result
        except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
            raise persistence.PersistenceError(f"Could not validate project spectra: {error}") from error

    def save_comparison(self, name: str, record: dict) -> Path:
        """Persist a verified comparison record inside the project directory."""
        try:
            return save_comparison_record(name, self.root, record)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise persistence.PersistenceError(f"Could not save comparison record: {error}") from error

    def comparisons(self, name: str) -> tuple[list, int]:
        """Return `(valid_records, invalid_count)` for saved comparison records in `name`."""
        try:
            return load_comparison_records(name, self.root)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise persistence.PersistenceError(f"Could not load comparison records: {error}") from error
