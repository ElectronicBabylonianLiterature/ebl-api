from ebl.fragmentarium.application.archaeology_schemas import (
    ArchaeologySchema,
    ExcavationNumberSchema,
    FindspotSchema,
)
from ebl.fragmentarium.application.date_schemas import DateWithNotesSchema
from ebl.tests.factories.archaeology import (
    ArchaeologyFactory,
    ExcavationPlanFactory,
    FindspotFactory,
)
from ebl.tests.factories.bibliography import ReferenceFactory


def test_serialize_archaeology():
    archaeology = ArchaeologyFactory.build()

    assert ArchaeologySchema().dump(archaeology) == {
        "excavationNumber": ExcavationNumberSchema().dump(
            archaeology.excavation_number
        ),
        "site": archaeology.site.long_name,
        "regularExcavation": archaeology.regular_excavation,
        "excavationDate": DateWithNotesSchema().dump(
            archaeology.excavation_date, many=True
        ),
        "findspot": FindspotSchema().dump(archaeology.findspot),
    }


def test_deserialize_archaeology():
    references = (ReferenceFactory.build(with_document=False),)
    plan_references = (ReferenceFactory.build(with_document=False),)

    plans = (ExcavationPlanFactory.build(references=plan_references),)
    findspot = FindspotFactory.build(references=references, plans=plans)

    archaeology = ArchaeologyFactory.build(findspot=findspot)

    assert (
        ArchaeologySchema().load(
            {
                "excavationNumber": ExcavationNumberSchema().dump(
                    archaeology.excavation_number
                ),
                "site": archaeology.site.long_name,
                "regularExcavation": archaeology.regular_excavation,
                "excavationDate": DateWithNotesSchema().dump(
                    archaeology.excavation_date, many=True
                ),
                "findspot": FindspotSchema().dump(archaeology.findspot),
            }
        )
        == archaeology
    )
