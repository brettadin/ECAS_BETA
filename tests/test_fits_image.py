"""Tests for 2D FITS image scanning, targeted plane reading, statistics, and UI viewer."""
from pathlib import Path
from unittest.mock import patch
import struct
import numpy as np
import pytest
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QMessageBox

from ecas.ingestion.csv_importer import SpectrumImportError
from ecas.ingestion.fits_image import (
    FitsImageContainer,
    FitsImagePlane,
    apply_display_stretch,
    compute_plane_statistics,
    read_fits_image_plane,
    scan_fits_image,
)
from ecas.ingestion.tabular_formats import import_fits_bintable_spectrum
from ecas.ui.fits_image_viewer import FitsImageViewerDialog
from ecas.ui.main_window import ECASWindow


def card(key: str, value: str = "") -> bytes:
    return ((f"{key:<8}= {value}" if key != "END" else "END").ljust(80)).encode("ascii")


def header(pairs: list[tuple[str, str]]) -> bytes:
    raw = b"".join(card(k, v) for k, v in pairs) + card("END")
    return raw.ljust((len(raw) + 2879) // 2880 * 2880, b" ")


@pytest.fixture
def synthetic_fits_image(tmp_path: Path) -> Path:
    """Create a synthetic multi-HDU 2D FITS image container with real physical scaling."""
    path = tmp_path / "synthetic_jwst_miri.fits"

    # Primary HDU: NAXIS=0, instrument/target metadata
    primary_hdr = header([
        ("SIMPLE", "T"),
        ("BITPIX", "8"),
        ("NAXIS", "0"),
        ("EXTEND", "T"),
        ("TELESCOP", "'JWST'"),
        ("INSTRUME", "'MIRI'"),
        ("DETECTOR", "'MIRIMAGE'"),
        ("FILTER", "'F770W'"),
        ("TARGNAME", "'JUPITER'"),
        ("DATE-OBS", "'2022-07-03'"),
        ("EFFEXPTM", "30.525"),
        ("S_PHOTOM", "'COMPLETE'"),
        ("S_RAMP", "'COMPLETE'"),
        ("S_OUTLIR", "'SKIPPED'"),
    ])

    # HDU 1: SCI image (100 x 50, float32, MJy/sr)
    # NAXIS1=100 (width / cols), NAXIS2=50 (height / rows)
    # Include a CONTINUE card chain to test long strings like S_REGION
    region_1 = card("S_REGION", "'POLYGON ICRS 10.0 20.0 30.0 40.0 &'")
    region_2 = card("CONTINUE", "'50.0 60.0 &'")
    region_3 = card("CONTINUE", "'70.0 80.0'")

    sci_cards = [
        ("XTENSION", "'IMAGE'"),
        ("BITPIX", "-32"),
        ("NAXIS", "2"),
        ("NAXIS1", "100"),
        ("NAXIS2", "50"),
        ("PCOUNT", "0"),
        ("GCOUNT", "1"),
        ("EXTNAME", "'SCI'"),
        ("BUNIT", "'MJy/sr'"),
    ]
    cards_raw = b"".join(card(k, v) for k, v in sci_cards) + region_1 + region_2 + region_3 + card("END")
    raw_sci = cards_raw.ljust((len(cards_raw) + 2879) // 2880 * 2880, b" ")

    # Generate synthetic float32 flux values with a central Gaussian-like peak and some NaNs
    sci_arr = np.zeros((50, 100), dtype=">f4")
    y, x = np.ogrid[:50, :100]
    sci_arr[:] = 10.0 + 50.0 * np.exp(-((x - 50) ** 2 + (y - 25) ** 2) / 200.0)
    sci_arr[0, 0] = np.nan  # inject a bad pixel
    sci_data = sci_arr.tobytes().ljust((sci_arr.nbytes + 2879) // 2880 * 2880, b"\0")

    # HDU 2: DQ bitmask image (100 x 50, int32)
    dq_hdr = header([
        ("XTENSION", "'IMAGE'"),
        ("BITPIX", "32"),
        ("NAXIS", "2"),
        ("NAXIS1", "100"),
        ("NAXIS2", "50"),
        ("PCOUNT", "0"),
        ("GCOUNT", "1"),
        ("EXTNAME", "'DQ'"),
        ("BUNIT", "''"),
    ])
    dq_arr = np.zeros((50, 100), dtype=">i4")
    dq_arr[0, 0] = 1  # DO_NOT_USE
    dq_arr[25, 50] = 2  # SATURATED
    dq_data = dq_arr.tobytes().ljust((dq_arr.nbytes + 2879) // 2880 * 2880, b"\0")

    with path.open("wb") as stream:
        stream.write(primary_hdr)
        stream.write(raw_sci)
        stream.write(sci_data)
        stream.write(dq_hdr)
        stream.write(dq_data)

    return path


def test_fits_image_scan(synthetic_fits_image: Path):
    """Test header scanning without loading image arrays into memory."""
    container = scan_fits_image(synthetic_fits_image)
    assert container is not None
    assert container.target_name == "JUPITER"
    assert container.telescope == "JWST"
    assert container.instrument == "MIRI"
    assert container.detector == "MIRIMAGE"
    assert container.filter_name == "F770W"
    assert container.date_obs == "2022-07-03"
    assert container.exposure_time_sec == pytest.approx(30.525)
    assert "S_PHOTOM=COMPLETE" in container.pipeline_stage
    assert container.product_summary == "JWST MIRI F770W"

    assert len(container.planes) == 2
    sci = container.planes[0]
    assert sci.extname == "SCI"
    assert sci.width == 100
    assert sci.height == 50
    assert sci.bitpix == -32
    assert sci.bunit == "MJy/sr"
    assert sci.display_label == "SCI (100 x 50 [MJy/sr])"

    dq = container.planes[1]
    assert dq.extname == "DQ"
    assert dq.width == 100
    assert dq.height == 50
    assert dq.bitpix == 32


def test_fits_image_plane_read(synthetic_fits_image: Path):
    """Test extracting specific 2D planes and verifying numerical integrity."""
    container = scan_fits_image(synthetic_fits_image)
    assert container is not None

    sci_plane = container.default_plane
    assert sci_plane is not None
    arr = read_fits_image_plane(synthetic_fits_image, sci_plane)
    assert arr.shape == (50, 100)
    assert arr.dtype == np.float32
    assert np.isnan(arr[0, 0])
    assert arr[25, 50] > 55.0  # Gaussian peak

    dq_plane = container.planes[1]
    dq_arr = read_fits_image_plane(synthetic_fits_image, dq_plane)
    assert dq_arr.shape == (50, 100)
    assert dq_arr.dtype == np.int32
    assert dq_arr[0, 0] == 1
    assert dq_arr[25, 50] == 2
    assert dq_arr[10, 10] == 0


def test_compute_plane_statistics(synthetic_fits_image: Path):
    """Test robust computation of image statistics including NaNs."""
    container = scan_fits_image(synthetic_fits_image)
    assert container is not None
    arr = read_fits_image_plane(synthetic_fits_image, container.default_plane)

    stats = compute_plane_statistics(arr)
    assert stats["total_pixels"] == 5000
    assert stats["nan_count"] == 1
    assert stats["finite_min"] == pytest.approx(10.0, abs=0.1)
    assert stats["finite_max"] > 55.0
    assert stats["median"] == pytest.approx(10.0, abs=1.0)
    assert stats["p01"] <= stats["median"] <= stats["p99"]


def test_apply_display_stretch(synthetic_fits_image: Path):
    """Test display stretches without altering the input array."""
    container = scan_fits_image(synthetic_fits_image)
    assert container is not None
    arr = read_fits_image_plane(synthetic_fits_image, container.default_plane)
    orig_copy = arr.copy()

    for stretch in ("asinh", "percentile", "minmax", "sqrt", "log"):
        disp, vmin, vmax = apply_display_stretch(arr, stretch)
        assert disp.shape == arr.shape
        assert vmin <= vmax
        # Verify original scientific array was not mutated
        np.testing.assert_array_equal(np.isnan(arr), np.isnan(orig_copy))
        np.testing.assert_allclose(arr[np.isfinite(arr)], orig_copy[np.isfinite(orig_copy)])


def test_bintable_importer_rejects_image_with_rich_diagnostic(synthetic_fits_image: Path):
    """Verify that attempting to import an image as a 1D spectrum fails with clear guidance."""
    with pytest.raises(SpectrumImportError) as exc_info:
        import_fits_bintable_spectrum(synthetic_fits_image)

    err = str(exc_info.value)
    assert "2D astronomical image container" in err
    assert "JWST MIRI F770W" in err
    assert "JUPITER" in err
    assert "100 x 50 pixels" in err
    assert "unit: MJy/sr" in err
    assert "not a 1D sampled spectrum" in err


def test_fits_image_viewer_dialog(synthetic_fits_image: Path):
    """Test FitsImageViewerDialog lifecycle, plane switching, and mouse coordinates."""
    app = QApplication.instance() or QApplication([])

    dialog = FitsImageViewerDialog(synthetic_fits_image)
    dialog.show()

    assert dialog.lbl_target.text() == "JUPITER"
    assert dialog.lbl_product.text() == "JWST MIRI F770W"
    assert dialog.cmb_plane.count() == 2

    # Verify default SCI plane loaded
    assert dialog.current_plane.extname == "SCI"
    assert dialog.current_raw_data is not None
    assert dialog.current_raw_data.shape == (50, 100)

    # Switch to DQ plane
    dialog.cmb_plane.setCurrentIndex(1)
    assert dialog.current_plane.extname == "DQ"
    assert dialog.current_raw_data.dtype == np.int32

    # Switch stretch
    dialog.cmb_stretch.setCurrentIndex(2)  # Min - Max

    # Switch colormap
    dialog.cmb_colormap.setCurrentText("viridis")

    # Simulate mouse movement over pixel (50, 25)
    view_box = dialog.image_view.getView()
    scene_pt = view_box.mapViewToScene(QPointF(50.5, 25.5))
    dialog._on_mouse_moved(scene_pt)

    cursor_text = dialog.lbl_cursor.text()
    assert "Pixel: (X: 50, Y: 25)" in cursor_text
    assert "Value: 2" in cursor_text  # DQ saturated bit

    dialog.accept()
    dialog.close()


def test_main_window_intercepts_image_fits_import(synthetic_fits_image: Path):
    """Test that importing a 2D FITS image in ECASWindow triggers the image detection handler."""
    app = QApplication.instance() or QApplication([])

    with patch("ecas.ui.main_window.QMessageBox") as mock_msg_box_cls, \
         patch.object(ECASWindow, "_open_fits_image_viewer") as mock_viewer:

        mock_box = mock_msg_box_cls.return_value
        mock_box.exec.return_value = 0
        mock_box.clickedButton.return_value = None

        win = ECASWindow()
        # Trigger import error with synthetic image
        win._import_csv_from_path(str(synthetic_fits_image))

        # Status bar should indicate import failed as spectrum
        assert win.statusBar().currentMessage() == "Import failed"
        assert win.current_spectrum is None
        mock_msg_box_cls.assert_called()
        win.close()


@pytest.mark.parametrize(
    "fname,expected_planes,expected_unit",
    [
        (
            "jw01022017001_03101_00001_mirimage_rate.fits",
            ["SCI", "ERR", "DQ", "VAR_POISSON", "VAR_RNOISE"],
            "DN/s",
        ),
        (
            "jw01022017001_03101_00001_mirimage_o017_crf.fits",
            ["SCI", "ERR", "DQ", "AREA", "VAR_POISSON", "VAR_RNOISE", "VAR_FLAT"],
            "MJy/sr",
        ),
    ],
)
def test_real_jupiter_miri_files_in_downloads(fname: str, expected_planes: list[str], expected_unit: str):
    """Verify scanning and reading of actual user JWST MIRI files if present in Downloads."""
    downloads = Path(r"C:\Users\Blake\Downloads")
    fpath = downloads / fname
    if not fpath.exists():
        pytest.skip(f"Local file {fname} not found in Downloads")

    container = scan_fits_image(fpath)
    assert container is not None
    assert container.target_name == "JUPITER"
    assert container.product_summary == "JWST MIRI F770W"
    assert [p.extname for p in container.planes] == expected_planes

    sci_plane = container.default_plane
    assert sci_plane is not None
    assert sci_plane.width == 1032
    assert sci_plane.height == 1024
    assert sci_plane.bunit == expected_unit

    arr = read_fits_image_plane(fpath, sci_plane)
    assert arr.shape == (1024, 1032)
    assert arr.dtype == np.float32

    stats = compute_plane_statistics(arr)
    assert stats["total_pixels"] == 1032 * 1024
    assert np.isfinite(stats["median"])
    assert stats["finite_min"] < stats["finite_max"]

