import pytest
from ebl.dossiers.domain.dossier_record import (
    DossierRecord,
)
from ebl.dossiers.infrastructure.mongo_dossiers_repository import (
    DossierRecordSchema,
)
from ebl.tests.factories.dossier import DossierRecordFactory
from ebl.fragmentarium.domain.fragment import Script
from ebl.common.domain.provenance import Provenance
from ebl.fragmentarium.application.fragment_fields_schemas import ScriptSchema
from ebl.bibliography.application.reference_schema import ApiReferenceSchema


@pytest.fixture
def dossier_record():
    return DossierRecordFactory.build()


def test_dossier_record_creation(
    dossier_record: DossierRecord,
) -> None:
    assert dossier_record.id is not None
    assert isinstance(dossier_record.description, (str, type(None)))
    assert isinstance(dossier_record.is_approximate_date, (bool, type(None)))
    assert isinstance(dossier_record.year_range_from, (float, int, type(None)))
    assert isinstance(dossier_record.year_range_to, (float, int, type(None)))
    assert isinstance(dossier_record.related_kings, (list, type(None)))
    assert isinstance(dossier_record.provenance, (Provenance, type(None)))
    assert isinstance(dossier_record.script, (Script, type(None)))
    assert isinstance(dossier_record.references, (tuple, type(None)))


def test_dossier_record_defaults() -> None:
    blank_dossier_record = DossierRecord("test id")

    assert blank_dossier_record.id == "test id"
    assert blank_dossier_record.description is None
    assert blank_dossier_record.is_approximate_date is False
    assert blank_dossier_record.year_range_from is None
    assert blank_dossier_record.year_range_to is None
    assert blank_dossier_record.related_kings == []
    assert blank_dossier_record.provenance is None
    assert blank_dossier_record.script is None
    assert blank_dossier_record.references == ()


def test_dossier_record_to_dict(
    dossier_record: DossierRecord,
) -> None:
    assert DossierRecordSchema().dump(dossier_record) == {
        "_id": dossier_record.id,
        "description": dossier_record.description,
        "isApproximateDate": dossier_record.is_approximate_date,
        "yearRangeFrom": dossier_record.year_range_from,
        "yearRangeTo": dossier_record.year_range_to,
        "relatedKings": dossier_record.related_kings,
        "provenance": dossier_record.provenance.long_name
        if dossier_record.provenance
        else None,
        "script": ScriptSchema().dump(dossier_record.script),
        "references": ApiReferenceSchema().dump(dossier_record.references, many=True),
    }


def test_dossier_record_from_dict(
    dossier_record: DossierRecord,
) -> None:
    serialized_data = DossierRecordSchema().dump(dossier_record)
    deserialized_object = DossierRecordSchema().load(serialized_data)

    assert deserialized_object.id == dossier_record.id
    assert deserialized_object.description == dossier_record.description
    assert deserialized_object.is_approximate_date == dossier_record.is_approximate_date
    assert deserialized_object.year_range_from == dossier_record.year_range_from
    assert deserialized_object.year_range_to == dossier_record.year_range_to
    assert deserialized_object.related_kings == dossier_record.related_kings
    assert deserialized_object.provenance == dossier_record.provenance
    assert deserialized_object.script == dossier_record.script
    assert deserialized_object.references == dossier_record.references
