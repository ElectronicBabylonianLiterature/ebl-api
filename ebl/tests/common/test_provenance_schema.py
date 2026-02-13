from ebl.common.domain.provenance_model import GeoCoordinate, ProvenanceRecord
from ebl.common.application.provenance_schema import (
    GeoCoordinateSchema,
    ProvenanceRecordSchema,
    ApiProvenanceRecordSchema,
)


def test_geo_coordinate_schema_serialize():
    coord = GeoCoordinate(
        latitude=32.5,
        longitude=44.4,
        uncertainty_radius_km=0.5,
        notes="Test note",
    )
    schema = GeoCoordinateSchema()
    result = schema.dump(coord)

    assert result == {
        "latitude": 32.5,
        "longitude": 44.4,
        "uncertaintyRadiusKm": 0.5,
        "notes": "Test note",
    }


def test_geo_coordinate_schema_serialize_minimal():
    coord = GeoCoordinate(latitude=32.5, longitude=44.4)
    schema = GeoCoordinateSchema()
    result = schema.dump(coord)

    assert result == {
        "latitude": 32.5,
        "longitude": 44.4,
    }


def test_geo_coordinate_schema_deserialize():
    data = {
        "latitude": 32.5,
        "longitude": 44.4,
        "uncertaintyRadiusKm": 0.5,
        "notes": "Test note",
    }
    schema = GeoCoordinateSchema()
    result = schema.load(data)

    assert result.latitude == 32.5
    assert result.longitude == 44.4
    assert result.uncertainty_radius_km == 0.5
    assert result.notes == "Test note"


def test_provenance_record_schema_serialize():
    coord = GeoCoordinate(latitude=32.5, longitude=44.4)
    record = ProvenanceRecord(
        id="BABYLON",
        long_name="Babylon",
        abbreviation="Bab",
        parent="BABYLONIA",
        cigs_key="BAB",
        sort_key=1,
        coordinates=coord,
    )
    schema = ProvenanceRecordSchema()
    result = schema.dump(record)

    assert result == {
        "_id": "BABYLON",
        "longName": "Babylon",
        "abbreviation": "Bab",
        "parent": "BABYLONIA",
        "cigsKey": "BAB",
        "sortKey": 1,
        "coordinates": {
            "latitude": 32.5,
            "longitude": 44.4,
        },
    }


def test_provenance_record_schema_serialize_minimal():
    record = ProvenanceRecord(
        id="TEST",
        long_name="Test",
        abbreviation="Tst",
    )
    schema = ProvenanceRecordSchema()
    result = schema.dump(record)

    assert result == {
        "_id": "TEST",
        "longName": "Test",
        "abbreviation": "Tst",
        "sortKey": -1,
    }


def test_provenance_record_schema_deserialize():
    data = {
        "_id": "BABYLON",
        "longName": "Babylon",
        "abbreviation": "Bab",
        "parent": "BABYLONIA",
        "cigsKey": "BAB",
        "sortKey": 1,
        "coordinates": {
            "latitude": 32.5,
            "longitude": 44.4,
        },
    }
    schema = ProvenanceRecordSchema()
    result = schema.load(data)

    assert result.id == "BABYLON"
    assert result.long_name == "Babylon"
    assert result.abbreviation == "Bab"
    assert result.parent == "BABYLONIA"
    assert result.cigs_key == "BAB"
    assert result.sort_key == 1
    assert result.coordinates.latitude == 32.5
    assert result.coordinates.longitude == 44.4


def test_api_provenance_record_schema():
    record = ProvenanceRecord(
        id="BABYLON",
        long_name="Babylon",
        abbreviation="Bab",
    )
    schema = ApiProvenanceRecordSchema()
    result = schema.dump(record)

    assert result["id"] == "BABYLON"
    assert result["longName"] == "Babylon"
    assert result["abbreviation"] == "Bab"
