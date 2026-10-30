
import pytest

from ecas.ingestion.csv_importer import (
    SpectrumImportError,
    WASP39B_SCHEMA,
)
from ecas.ingestion.import_manager import import_spectrum


def test_import_manager_rejects_unsupported_format(tmp_path):
    source = tmp_path / "spectrum.bin"
    source.write_text("wavelength signal\n1.0 2.0\n", encoding="utf-8")

    with pytest.raises(SpectrumImportError, match="Unsupported file format"):
        import_spectrum(source)


def test_import_manager_rejects_file_without_extension(tmp_path):
    source = tmp_path / "spectrum"
    source.write_text("wavelength,signal\n1.0,2.0\n", encoding="utf-8")

    with pytest.raises(SpectrumImportError, match="Unsupported file format"):
        import_spectrum(source)


def test_import_manager_imports_generic_csv(tmp_path):
    source = tmp_path / "spectrum.csv"
    source.write_text(
        "wavelength,signal\n1.0,2.0\n2.0,3.0\n",
        encoding="utf-8",
    )

    result = import_spectrum(source)

    assert result.source_file == source.resolve()
    assert result.columns == ("wavelength", "signal")
    assert result.row_count == 2
    assert result.rows[0]["wavelength"] == 1.0
    assert result.rows[0]["signal"] == 2.0


def test_import_manager_passes_archive_schema_to_csv_importer(tmp_path):
    source = tmp_path / "archive.csv"
    source.write_text(
        "centralwavelng,bandwidth,pl_trandep,pl_trandeperr1,"
        "pl_trandeperr2,pl_trandep_authors,pl_ratror,pl_ratrorerr1,"
        "pl_ratrorerr2,pl_ratror_authors,pl_radj,pl_radjerr1,"
        "pl_radjerr2,pl_radj_authors,pl_tranmid,pl_tranmiderr1,"
        "pl_tranmiderr2,st_rad,st_raderr1,st_raderr2,st_rad_authors\n"
        "1.0,0.1,0.02,0.001,-0.001,author,0.1,0.01,-0.01,"
        "author,1.0,0.1,-0.1,author,2450000,0.1,-0.1,"
        "1.0,0.1,-0.1,author\n",
        encoding="utf-8",
    )

    result = import_spectrum(source, archive_schema=WASP39B_SCHEMA)

    assert result.row_count == 1
    assert result.rows[0]["wavelength"] == 1.0
    assert result.rows[0]["signal"] == 0.02
