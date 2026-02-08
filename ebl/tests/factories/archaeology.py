from ebl.fragmentarium.domain.archaeology import Archaeology, ExcavationNumber
from ebl.fragmentarium.domain.date_range import DateRange, PartialDate
from ebl.fragmentarium.domain.findspot import (
    BuildingType,
    ExcavationPlan,
    ExcavationSite,
    Findspot,
)
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.collections import TupleFactory

import factory.fuzzy

FINDSPOT_COUNT = 3


class PartialDateFactory(factory.Factory):
    class Meta:
        model = PartialDate

    year = factory.fuzzy.FuzzyInteger(1900, 2020)
    month = factory.fuzzy.FuzzyChoice([*range(1, 13), None])
    day = factory.Maybe(
        "month",
        yes_declaration=factory.fuzzy.FuzzyChoice([*range(1, 29), None]),
        no_declaration=None,
    )
    notes = factory.Faker("sentence")


class DateRangeFactory(factory.Factory):
    class Meta:
        model = DateRange

    start = factory.SubFactory(PartialDateFactory)
    end = factory.SubFactory(PartialDateFactory)
    notes = factory.Faker("sentence")


class ExcavationPlanFactory(factory.Factory):
    class Meta:
        model = ExcavationPlan

    svg = "<svg></svg>"
    references = factory.List([factory.SubFactory(ReferenceFactory)], TupleFactory)


class FindspotFactory(factory.Factory):
    class Meta:
        model = Findspot

    id_ = factory.Sequence(lambda n: (n % FINDSPOT_COUNT) + 1)
    site = factory.fuzzy.FuzzyChoice(
        set(ExcavationSite) - {ExcavationSite.STANDARD_TEXT}
    )
    sector = factory.Faker("word")
    area = factory.Faker("word")
    building = factory.Faker("word")
    building_type = factory.fuzzy.FuzzyChoice(set(BuildingType))
    lavel_layer_phase = factory.Faker("word")
    date_range = factory.SubFactory(DateRangeFactory)
    plans = factory.List([factory.SubFactory(ExcavationPlanFactory)], TupleFactory)
    room = factory.Faker("word")
    context = factory.Faker("word")
    primary_context = factory.Faker("boolean")
    notes = factory.Faker("sentence")


class ArchaeologyFactory(factory.Factory):
    class Meta:
        model = Archaeology

    excavation_number = factory.Sequence(lambda n: ExcavationNumber("X", str(n)))
    site = factory.fuzzy.FuzzyChoice(
        set(ExcavationSite) - {ExcavationSite.STANDARD_TEXT}
    )
    regular_excavation = factory.Faker("boolean")
    excavation_date = factory.SubFactory(DateRangeFactory)

    class Params:
        with_findspot = factory.Trait(
            findspot=factory.SubFactory(FindspotFactory),
            findspot_id=factory.SelfAttribute("findspot.id_"),
        )
