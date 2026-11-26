from typing import Any, cast

import attr
import pytest
from marshmallow import ValidationError

from ebl.corpus.application.schemas import ManuscriptSchema
from ebl.corpus.infrastructure.stored_manuscript_schemas import StoredManuscriptSchema
from ebl.corpus.web.chapter_manuscript_schemas import ApiManuscriptSchema
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.tests.factories.corpus import ManuscriptFactory
from ebl.tests.factories.bibliography import ReferenceFactory


METADATA_FIELDS = ("siglumDisambiguator", "accession", "notes", "references")


@pytest.mark.parametrize(
    "missing", [*((field,) for field in METADATA_FIELDS), METADATA_FIELDS]
)
def test_stored_manuscript_defaults_only_absent_metadata(
    seeded_provenance_service: ProvenanceService, missing: tuple[str, ...]
) -> None:
    schema = StoredManuscriptSchema(
        context={"provenance_service": seeded_provenance_service}
    )
    manuscript = ManuscriptFactory.build(references=(ReferenceFactory.build(),))
    payload = cast(dict[str, Any], schema.dump(manuscript))
    for field in missing:
        del payload[field]
    expected = attr.evolve(
        manuscript,
        **{
            field: value
            for field, key, value in (
                ("siglum_disambiguator", "siglumDisambiguator", ""),
                ("accession", "accession", ""),
                ("notes", "notes", ""),
                ("references", "references", ()),
            )
            if key in missing
        },
    )
    original = payload.copy()
    assert schema.load(payload) == expected
    assert payload == original


def test_stored_manuscript_preserves_present_metadata(
    seeded_provenance_service: ProvenanceService,
) -> None:
    schema = StoredManuscriptSchema(
        context={"provenance_service": seeded_provenance_service}
    )
    manuscript = ManuscriptFactory.build(
        siglum_disambiguator="a",
        accession="ABC",
        museum_number=None,
        notes="note",
        references=(ReferenceFactory.build(),),
    )
    assert schema.load(cast(dict[str, Any], schema.dump(manuscript))) == manuscript


@pytest.mark.parametrize("field", METADATA_FIELDS)
@pytest.mark.parametrize("schema_class", [ManuscriptSchema, ApiManuscriptSchema])
def test_client_manuscript_metadata_remains_required(
    seeded_provenance_service: ProvenanceService,
    field: str,
    schema_class: type[ManuscriptSchema],
) -> None:
    schema = schema_class(context={"provenance_service": seeded_provenance_service})
    payload = cast(
        dict[str, Any],
        schema.dump(ManuscriptFactory.build(references=(ReferenceFactory.build(),))),
    )
    del payload[field]
    with pytest.raises(ValidationError) as error:
        schema.load(payload)
    assert cast(dict[str, list[str]], error.value.messages)[field] == [
        "Missing data for required field."
    ]


@pytest.mark.parametrize(
    "field", [*METADATA_FIELDS, "id", "museumNumber", "period", "provenance", "type"]
)
def test_storage_defaults_do_not_hide_invalid_or_required_fields(
    seeded_provenance_service: ProvenanceService,
    field: str,
) -> None:
    schema = StoredManuscriptSchema(
        context={"provenance_service": seeded_provenance_service}
    )
    payload = cast(
        dict[str, Any],
        schema.dump(ManuscriptFactory.build(references=(ReferenceFactory.build(),))),
    )
    if field in METADATA_FIELDS:
        payload[field] = None
    else:
        del payload[field]
    with pytest.raises(ValidationError) as error:
        schema.load(payload)
    assert field in error.value.messages
