import pytest
from marshmallow import Schema, ValidationError

from ebl.common.application.schemas import deserialize_provenance_record
from ebl.provenance.application.provenance_service import ProvenanceService


@pytest.mark.parametrize(
    "value", [{"name": "Assur"}, ["Assur"], {}, [], False, True, 0, 42]
)
def test_provenance_schema_rejects_non_strings(value: object) -> None:
    with pytest.raises(ValidationError, match="Provenance must be a string or null"):
        deserialize_provenance_record(Schema(), value)


@pytest.mark.parametrize("value", [None, ""])
def test_provenance_schema_preserves_empty_values(value: object) -> None:
    assert deserialize_provenance_record(Schema(), value) is None


def test_provenance_schema_requires_service() -> None:
    with pytest.raises(ValidationError, match="Provenance service not configured"):
        deserialize_provenance_record(Schema(), "Assur")


def test_provenance_schema_resolves_known_record(
    seeded_provenance_service: ProvenanceService,
) -> None:
    schema = Schema(context={"provenance_service": seeded_provenance_service})

    assert deserialize_provenance_record(schema, "Assur") == (
        seeded_provenance_service.find_by_id("ASSUR")
    )


def test_provenance_schema_rejects_unknown_record(
    seeded_provenance_service: ProvenanceService,
) -> None:
    schema = Schema(context={"provenance_service": seeded_provenance_service})

    with pytest.raises(ValidationError, match="Invalid provenance: Unknown"):
        deserialize_provenance_record(schema, "Unknown")
