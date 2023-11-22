from ebl.fragmentarium.domain.archaeology import Archaeology, ExcavationNumber
from ebl.fragmentarium.domain.iso_date import DateRange, DateWithNotes
from ebl.fragmentarium.domain.findspot import BuildingType, ExcavationPlan, Findspot
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.collections import TupleFactory
from ebl.corpus.domain.provenance import Provenance as ExcavationSite
import factory.fuzzy

FINDSPOT_COUNT = 3


class DateRangeFactory(factory.Factory):
    class Meta:
        model = DateRange

    start = factory.fuzzy.FuzzyInteger(-800, -750)
    end = factory.fuzzy.FuzzyInteger(-745, -650)
    notes = factory.Faker("sentence")


class DateWithNotesFactory(factory.Factory):
    class Meta:
        model = DateWithNotes

    date = factory.Faker("date_object")
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
    excavation_date = factory.List(
        [factory.SubFactory(DateWithNotesFactory)], TupleFactory
    )
    findspot_id = factory.Sequence(lambda n: (n % FINDSPOT_COUNT) + 1)
