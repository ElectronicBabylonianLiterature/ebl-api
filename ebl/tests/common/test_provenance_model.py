import pytest

from ebl.common.domain.provenance_model import GeoCoordinate, ProvenanceRecord


def test_geo_coordinate_valid():
    coord = GeoCoordinate(latitude=32.5, longitude=44.4)
    assert coord.latitude == 32.5
    assert coord.longitude == 44.4
    assert coord.uncertainty_radius_km is None
    assert coord.notes is None


def test_geo_coordinate_with_optional_fields():
    coord = GeoCoordinate(
        latitude=32.5,
        longitude=44.4,
        uncertainty_radius_km=0.5,
        notes="Approximate location",
    )
    assert coord.uncertainty_radius_km == 0.5
    assert coord.notes == "Approximate location"


def test_geo_coordinate_invalid_latitude():
    with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
        GeoCoordinate(latitude=91, longitude=44.4)

    with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
        GeoCoordinate(latitude=-91, longitude=44.4)


def test_geo_coordinate_invalid_longitude():
    with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
        GeoCoordinate(latitude=32.5, longitude=181)

    with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
        GeoCoordinate(latitude=32.5, longitude=-181)


def test_geo_coordinate_negative_uncertainty():
    with pytest.raises(ValueError, match="Uncertainty radius must be non-negative"):
        GeoCoordinate(latitude=32.5, longitude=44.4, uncertainty_radius_km=-1)


def test_provenance_record():
    record = ProvenanceRecord(
        id="BABYLON",
        long_name="Babylon",
        abbreviation="Bab",
        parent="BABYLONIA",
        cigs_key="BAB",
        sort_key=1,
    )
    assert record.id == "BABYLON"
    assert record.long_name == "Babylon"
    assert record.abbreviation == "Bab"
    assert record.parent == "BABYLONIA"
    assert record.cigs_key == "BAB"
    assert record.sort_key == 1
    assert record.coordinates is None


def test_provenance_record_with_coordinates():
    coord = GeoCoordinate(latitude=32.5, longitude=44.4)
    record = ProvenanceRecord(
        id="BABYLON",
        long_name="Babylon",
        abbreviation="Bab",
        coordinates=coord,
    )
    assert record.coordinates == coord


def test_provenance_record_minimal():
    record = ProvenanceRecord(
        id="TEST",
        long_name="Test",
        abbreviation="Tst",
    )
    assert record.id == "TEST"
    assert record.long_name == "Test"
    assert record.abbreviation == "Tst"
    assert record.parent is None
    assert record.cigs_key is None
    assert record.sort_key == -1
    assert record.coordinates is None
