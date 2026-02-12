import pytest
from ebl.fragmentarium.application.archaeology_schemas import (
    ArchaeologySchema,
    ExcavationNumberSchema,
    FindspotSchema,
)
from ebl.fragmentarium.application.date_schemas import DateRangeSchema
from ebl.fragmentarium.domain.archaeology import Archaeology
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
        "findspot": archaeology.findspot
        and findspot_schema.dump(archaeology.findspot),
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
            }
        )
        == archaeology
    )
