from typing import cast

import pytest
from marshmallow import ValidationError
from ebl.fragmentarium.application.archaeology_schemas import (
    ArchaeologyInputSchema,
    ArchaeologySchema,
    ExcavationNumberSchema,
    FindspotSchema,
)
from ebl.fragmentarium.application.date_schemas import DateRangeSchema
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.fragmentarium.domain.findspot import Findspot
from ebl.tests.factories.archaeology import (
    ArchaeologyFactory,
)


@pytest.mark.parametrize("with_findspot", [True, False])
def test_serialize_archaeology(with_findspot, seeded_provenance_service):
    archaeology: Archaeology = ArchaeologyFactory.build(with_findspot=with_findspot)

    schema = ArchaeologySchema(
        context={"provenance_service": seeded_provenance_service}
    )
    findspot_schema = FindspotSchema(
        context={"provenance_service": seeded_provenance_service}
    )

    assert schema.dump(archaeology) == {
        "excavationNumber": ExcavationNumberSchema().dump(
            archaeology.excavation_number
        ),
        "site": archaeology.site.long_name,
        "isRegularExcavation": archaeology.regular_excavation,
        "date": DateRangeSchema().dump(archaeology.excavation_date),
        "findspotId": archaeology.findspot_id,
        "findspot": archaeology.findspot and findspot_schema.dump(archaeology.findspot),
        "isFindspotUncertain": archaeology.is_findspot_uncertain,
    }


@pytest.mark.parametrize("with_findspot", [True, False])
def test_deserialize_archaeology(with_findspot, seeded_provenance_service):
    archaeology: Archaeology = ArchaeologyFactory.build(with_findspot=with_findspot)

    assert (
        ArchaeologySchema(
            context={"provenance_service": seeded_provenance_service}
        ).load(
            {
                "excavationNumber": ExcavationNumberSchema().dump(
                    archaeology.excavation_number
                ),
                "site": archaeology.site.long_name,
                "isRegularExcavation": archaeology.regular_excavation,
                "date": DateRangeSchema().dump(archaeology.excavation_date),
                "findspotId": archaeology.findspot_id,
                "findspot": archaeology.findspot
                and FindspotSchema(
                    context={"provenance_service": seeded_provenance_service}
                ).dump(archaeology.findspot),
                "isFindspotUncertain": archaeology.is_findspot_uncertain,
            }
        )
        == archaeology
    )


@pytest.mark.parametrize("empty_site_value", [None, ""])
def test_deserialize_archaeology_empty_site_returns_none(
    empty_site_value, seeded_provenance_service
):
    schema = ArchaeologySchema(
        context={"provenance_service": seeded_provenance_service}
    )
    result = cast(
        Archaeology,
        schema.load(
            {
                "excavationNumber": None,
                "site": empty_site_value,
                "isRegularExcavation": False,
            }
        ),
    )
    assert result.site is None


@pytest.mark.parametrize("empty_site_value", [None, ""])
def test_deserialize_findspot_empty_site_returns_none(
    empty_site_value, seeded_provenance_service
):
    schema = FindspotSchema(context={"provenance_service": seeded_provenance_service})
    result = cast(
        Findspot,
        schema.load(
            {
                "_id": 1,
                "site": empty_site_value,
            }
        ),
    )
    assert result.site is None


@pytest.mark.parametrize("with_findspot", [True, False])
def test_archaeology_input_accepts_existing_fields(
    with_findspot, seeded_provenance_service
) -> None:
    archaeology: Archaeology = ArchaeologyFactory.build(with_findspot=with_findspot)
    context = {"provenance_service": seeded_provenance_service}
    payload = cast(dict, ArchaeologySchema(context=context).dump(archaeology))

    assert ArchaeologyInputSchema(context=context).load(payload) == archaeology


@pytest.mark.parametrize(
    "payload",
    [
        {"findspot": {"_id": 1, "mapLocation": None}},
        {"unexpected": "value"},
    ],
)
def test_archaeology_input_rejects_unknown_fields(payload) -> None:
    with pytest.raises(ValidationError):
        ArchaeologyInputSchema().load(payload)
