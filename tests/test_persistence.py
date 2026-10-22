
"""Unit tests for the ECAS persistence module."""

from pathlib import Path

import pytest
from ecas.persistence import InvalidProjectIdError
from ecas.models.spectrum import SpectrumData
from ecas.persistence import (
    DatabaseNotFoundError,
    clear_project_database,
    count_spectra,
    load_spectra_from_database,
    load_spectrum_by_index,
    save_spectrum_to_database,
)


def make_spectrum(
    source_file=Path("sample.csv"),
    rows=None,
    columns=("wavelength", "signal"),
    axis_unit="nm",
    signal_unit="arbitrary units",
    signal_type=None,
    warnings=(),
):
    """Create a valid SpectrumData instance for persistence tests."""
    if rows is None:
        rows = (
            {"wavelength": 400.0, "signal": 0.25},
            {"wavelength": 500.0, "signal": 0.75},
        )

    return SpectrumData(
        source_file=Path(source_file),
        rows=tuple(rows),
        columns=tuple(columns),
        axis_unit=axis_unit,
        signal_unit=signal_unit,
        signal_type=signal_type,
        warnings=tuple(warnings),
    )


def assert_spectra_equal(original, loaded):
    """Verify that every SpectrumData field survives persistence."""
    assert loaded.source_file == original.source_file
    assert loaded.rows == original.rows
    assert loaded.columns == original.columns
    assert loaded.axis_unit == original.axis_unit
    assert loaded.signal_unit == original.signal_unit
    assert loaded.signal_type == original.signal_type
    assert loaded.warnings == original.warnings


class TestPersistenceRoundTrip:
    """Test saving and loading spectra."""

    def test_save_creates_database(self, tmp_path):
        projects_dir = tmp_path / "projects"
        project_id = "test_project"
        spectrum = make_spectrum()

        record_id = save_spectrum_to_database(
            spectrum, project_id, projects_dir
        )

        assert record_id == 1
        assert (
            projects_dir / project_id / "data.sqlite"
        ).exists()

    def test_round_trip_preserves_all_fields(self, tmp_path):
        projects_dir = tmp_path / "projects"
        project_id = "round_trip"
        original = make_spectrum(
            source_file=Path("data/experiment.csv"),
            rows=(
                {"wavelength": 410.0, "signal": 0.12},
                {"wavelength": 520.0, "signal": 0.98},
            ),
            columns=("wavelength", "signal"),
            axis_unit="nm",
            signal_unit="relative intensity",
            signal_type="transmission",
            warnings=("Example import warning",),
        )

        save_spectrum_to_database(
            original, project_id, projects_dir
        )
        loaded_spectra = load_spectra_from_database(
            project_id, projects_dir
        )

        assert len(loaded_spectra) == 1
        assert_spectra_equal(original, loaded_spectra[0])

    def test_column_order_is_preserved(self, tmp_path):
        projects_dir = tmp_path / "projects"
        project_id = "column_order"
        original = make_spectrum(
            rows=(
                {
                    "signal": 0.5,
                    "wavelength": 450.0,
                    "uncertainty": 0.02,
                },
            ),
            columns=("signal", "wavelength", "uncertainty"),
        )

        save_spectrum_to_database(
            original, project_id, projects_dir
        )
        loaded = load_spectra_from_database(
            project_id, projects_dir
        )[0]

        assert loaded.columns == (
            "signal",
            "wavelength",
            "uncertainty",
        )
        assert_spectra_equal(original, loaded)

    def test_none_values_are_preserved(self, tmp_path):
        projects_dir = tmp_path / "projects"
        project_id = "missing_values"
        original = make_spectrum(
            rows=(
                {
                    "wavelength": 400.0,
                    "signal": 0.5,
                    "uncertainty": None,
                },
                {
                    "wavelength": 500.0,
                    "signal": None,
                    "uncertainty": 0.03,
                },
            ),
            columns=("wavelength", "signal", "uncertainty"),
            warnings=(
                "Some measurements have missing values.",
            ),
        )

        save_spectrum_to_database(
            original, project_id, projects_dir
        )
        loaded = load_spectra_from_database(
            project_id, projects_dir
        )[0]

        assert loaded.rows[0]["uncertainty"] is None
        assert loaded.rows[1]["signal"] is None
        assert_spectra_equal(original, loaded)

    def test_absent_uncertainty_column_stays_absent(self, tmp_path):
        projects_dir = tmp_path / "projects"
        project_id = "no_uncertainty"
        original = make_spectrum(
            rows=(
                {"wavelength": 400.0, "signal": 0.5},
            ),
            columns=("wavelength", "signal"),
        )

        save_spectrum_to_database(
            original, project_id, projects_dir
        )
        loaded = load_spectra_from_database(
            project_id, projects_dir
        )[0]

        assert "uncertainty" not in loaded.columns
        assert "uncertainty" not in loaded.rows[0]
        assert_spectra_equal(original, loaded)

    def test_multiple_spectra_are_saved_and_loaded(self, tmp_path):
        projects_dir = tmp_path / "projects"
        project_id = "multiple_spectra"

        originals = [
            make_spectrum(
                source_file=Path(f"spectrum_{i}.csv"),
                rows=({"wavelength": float(i), "signal": 0.5},),
            )
            for i in range(1, 4)
        ]

        for spectrum in originals:
            save_spectrum_to_database(
                spectrum, project_id, projects_dir
            )

        loaded = load_spectra_from_database(
            project_id, projects_dir
        )

        assert len(loaded) == 3
        for original, restored in zip(originals, loaded):
            assert_spectra_equal(original, restored)

        assert count_spectra(project_id, projects_dir) == 3

    def test_load_spectrum_by_index(self, tmp_path):
        projects_dir = tmp_path / "projects"
        project_id = "indexed_load"
        original = make_spectrum()

        save_spectrum_to_database(
            original, project_id, projects_dir
        )

        loaded = load_spectrum_by_index(
            project_id, projects_dir, 0
        )
        assert loaded is not None
        assert_spectra_equal(original, loaded)

        assert (
            load_spectrum_by_index(
                project_id, projects_dir, 1
            )
            is None
        )


class TestPersistenceEdgeCases:
    """Test empty databases and database clearing."""

    def test_nonexistent_project_loads_as_empty_list(self, tmp_path):
        loaded = load_spectra_from_database(
            "nonexistent", tmp_path / "projects"
        )
        assert loaded == []

    def test_nonexistent_project_has_zero_spectra(self, tmp_path):
        count = count_spectra(
            "nonexistent", tmp_path / "projects"
        )
        assert count == 0

    def test_clear_database_removes_all_spectra(self, tmp_path):
        projects_dir = tmp_path / "projects"
        project_id = "clear_test"

        save_spectrum_to_database(
            make_spectrum(), project_id, projects_dir
        )
        assert count_spectra(project_id, projects_dir) == 1

        clear_project_database(project_id, projects_dir)

        assert count_spectra(project_id, projects_dir) == 0
        assert load_spectra_from_database(
            project_id, projects_dir
        ) == []

    def test_clearing_nonexistent_database_raises_error(self, tmp_path):
        with pytest.raises(DatabaseNotFoundError):
            clear_project_database(
                "nonexistent", tmp_path / "projects"
            )

class TestProjectIdValidation:
    """Test project ID and path validation."""

    @pytest.mark.parametrize(
        "project_id",
        [
            "",
            "../outside",
            "nested/project",
            "project name",
            ".",
            "project.name",
        ],
    )
    def test_rejects_invalid_project_ids(self, tmp_path, project_id):
        with pytest.raises(InvalidProjectIdError):
            save_spectrum_to_database(
                make_spectrum(),
                project_id,
                tmp_path / "projects",
            )

    def test_rejects_non_string_project_id(self, tmp_path):
        with pytest.raises(InvalidProjectIdError):
            save_spectrum_to_database(
                make_spectrum(),
                None,
                tmp_path / "projects",
            )

    def test_accepts_valid_project_id(self, tmp_path):
        projects_dir = tmp_path / "projects"

        save_spectrum_to_database(
            make_spectrum(),
            "valid_project-123",
            projects_dir,
        )

        assert (
            projects_dir / "valid_project-123" / "data.sqlite"
        ).exists()

    def test_rejects_symlink_that_escapes_projects_directory(self, tmp_path):
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()

        link = projects_dir / "linked_project"

        try:
            link.symlink_to(outside_dir, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("Directory symlink creation is unavailable.")

        with pytest.raises(InvalidProjectIdError):
            save_spectrum_to_database(
                make_spectrum(),
                "linked_project",
                projects_dir,
            )