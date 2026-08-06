from ebl.fragmentarium.domain.archaeology import Archaeology, ExcavationNumber
from ebl.fragmentarium.domain.date_range import DateRange, PartialDate
from ebl.fragmentarium.domain.findspot import (
    BuildingType,
    ExcavationPlan,
    Findspot,
)
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.provenance import DEFAULT_NON_STANDARD_PROVENANCES

import factory.fuzzy
from factory.declarations import (
    LazyAttribute,
    List,
    SelfAttribute,
    Sequence,
    SubFactory,
    Trait,
)
from factory.faker import Faker
from factory.helpers import make_factory
from factory.random import randgen

FINDSPOT_COUNT = 3
TUPLE_FACTORY = "ebl.tests.factories.collections.TupleFactory"


def _random_day(date: PartialDate) -> object:
    return randgen.choice([*range(1, 29), None]) if date.month else None


PartialDateFactory = make_factory(
    PartialDate,
    year=factory.fuzzy.FuzzyInteger(1900, 2020),
    month=factory.fuzzy.FuzzyChoice([*range(1, 13), None]),
    day=LazyAttribute(_random_day),
    notes=Faker("sentence"),
)

DateRangeFactory = make_factory(
    DateRange,
    start=SubFactory(PartialDateFactory),
    end=SubFactory(PartialDateFactory),
    notes=Faker("sentence"),
)

ExcavationPlanFactory = make_factory(
    ExcavationPlan,
    svg="<svg></svg>",
    references=List([SubFactory(ReferenceFactory)], TUPLE_FACTORY),
)

FindspotFactory = make_factory(
    Findspot,
    id_=Sequence(lambda n: (n % FINDSPOT_COUNT) + 1),
    site=factory.fuzzy.FuzzyChoice(DEFAULT_NON_STANDARD_PROVENANCES),
    sector=Faker("word"),
    area=Faker("word"),
    building=Faker("word"),
    building_type=factory.fuzzy.FuzzyChoice(set(BuildingType)),
    lavel_layer_phase=Faker("word"),
    date_range=SubFactory(DateRangeFactory),
    plans=List([SubFactory(ExcavationPlanFactory)], TUPLE_FACTORY),
    room=Faker("word"),
    context=Faker("word"),
    primary_context=Faker("boolean"),
    notes=Faker("sentence"),
)


class ArchaeologyParams:
    with_findspot = Trait(
        findspot=SubFactory(FindspotFactory),
        findspot_id=SelfAttribute("findspot.id_"),
    )


ArchaeologyFactory = make_factory(
    Archaeology,
    excavation_number=Sequence(lambda n: ExcavationNumber("EX", str(n))),
    site=factory.fuzzy.FuzzyChoice(DEFAULT_NON_STANDARD_PROVENANCES),
    regular_excavation=Faker("boolean"),
    excavation_date=SubFactory(DateRangeFactory),
    is_findspot_uncertain=Faker("boolean"),
    Params=ArchaeologyParams,
)
