from ebl.fragmentarium.domain.archaeology import Archaeology, ExcavationNumber
from ebl.fragmentarium.domain.date_range import DateRange, PartialDate
from ebl.fragmentarium.domain.findspot import (
    BuildingType,
    ExcavationPlan,
    Findspot,
)
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.collections import TupleFactory
from ebl.tests.factories.provenance import DEFAULT_NON_STANDARD_PROVENANCES

import factory.fuzzy
from factory.base import Factory
from factory.declarations import (
    List,
    Maybe,
    SelfAttribute,
    Sequence,
    SubFactory,
    Trait,
)
from factory.faker import Faker

FINDSPOT_COUNT = 3


class PartialDateFactory(Factory):
    class Meta:
        model = PartialDate

    year = factory.fuzzy.FuzzyInteger(1900, 2020)
    month = factory.fuzzy.FuzzyChoice([*range(1, 13), None])
    day = Maybe(
        "month",
        yes_declaration=factory.fuzzy.FuzzyChoice([*range(1, 29), None]),
        no_declaration=None,
    )
    notes = Faker("sentence")


class DateRangeFactory(Factory):
    class Meta:
        model = DateRange

    start = SubFactory(PartialDateFactory)
    end = SubFactory(PartialDateFactory)
    notes = Faker("sentence")


class ExcavationPlanFactory(Factory):
    class Meta:
        model = ExcavationPlan

    svg = "<svg></svg>"
    references = List([SubFactory(ReferenceFactory)], TupleFactory)


class FindspotFactory(Factory):
    class Meta:
        model = Findspot

    id_ = Sequence(lambda n: (n % FINDSPOT_COUNT) + 1)
    site = factory.fuzzy.FuzzyChoice(DEFAULT_NON_STANDARD_PROVENANCES)
    sector = Faker("word")
    area = Faker("word")
    building = Faker("word")
    building_type = factory.fuzzy.FuzzyChoice(set(BuildingType))
    lavel_layer_phase = Faker("word")
    date_range = SubFactory(DateRangeFactory)
    plans = List([SubFactory(ExcavationPlanFactory)], TupleFactory)
    room = Faker("word")
    context = Faker("word")
    primary_context = Faker("boolean")
    notes = Faker("sentence")


class ArchaeologyFactory(Factory):
    class Meta:
        model = Archaeology

    excavation_number = Sequence(lambda n: ExcavationNumber("X", str(n)))
    site = factory.fuzzy.FuzzyChoice(DEFAULT_NON_STANDARD_PROVENANCES)
    regular_excavation = Faker("boolean")
    excavation_date = SubFactory(DateRangeFactory)

    is_findspot_uncertain = Faker("boolean")

    class Params:
        with_findspot = Trait(
            findspot=SubFactory(FindspotFactory),
            findspot_id=SelfAttribute("findspot.id_"),
        )
