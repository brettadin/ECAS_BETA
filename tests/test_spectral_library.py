"""Import assertions against the unchanged, curated real project library."""
from pathlib import Path
import hashlib

from ecas.identification.library import discover_library, load_reference

ROOT = Path(__file__).resolve().parents[1] / "data" / "ECAS_Spectral_Library"


def test_discover_actual_library_and_condition_variants():
    catalog = discover_library(ROOT)
    assert catalog.issues == ()
    assert len(catalog.datasets) == 40
    assert sum(r.modality == "IR" for r in catalog.datasets) == 18
    assert sum(r.modality == "UV-Vis" for r in catalog.datasets) == 22
    assert len({r.dataset_id for r in catalog.datasets}) == 40
    water = [r for r in catalog.datasets if r.modality == "IR" and r.molecule == "H2O"]
    assert water and {r.metadata["phase"] for r in water} == {"gas", "liquid"}
    for ref in catalog.datasets:
        assert ref.source_sha256 == hashlib.sha256(ref.source_path.read_bytes()).hexdigest()
        assert ref.metadata["curation_manifest"]
        assert dict(ref.spectrum.metadata)["modality"] == ref.modality


def test_real_signed_uv_measurements_are_not_clipped():
    refs = [r for r in discover_library(ROOT).datasets if r.modality == "UV-Vis"]
    negative = [r for r in refs if any(row["signal"] < 0 for row in r.spectrum.rows)]
    assert len(negative) == 6
    assert all(any("negative" in warning for warning in r.spectrum.warnings) for r in negative)


def test_real_ir_values_above_unity_and_axis_units_retained():
    refs = discover_library(ROOT).datasets
    co2 = next(r for r in refs if r.modality == "IR" and r.source_path.name == "CO2_gas_IR_index1.jdx")
    assert max(row["signal"] for row in co2.spectrum.rows) > 1
    no = next(r for r in refs if r.modality == "IR" and r.molecule == "NO")
    assert no.spectrum.axis_unit == "microns"
    assert load_reference(no.source_path).spectrum.rows == no.spectrum.rows


def test_missing_library_is_reported(tmp_path):
    catalog = discover_library(tmp_path)
    assert not catalog.datasets and "missing" in catalog.issues[0].lower()
