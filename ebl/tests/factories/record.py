from factory.base import Factory
from factory.declarations import List, SubFactory
from factory.faker import Faker
from factory.fuzzy import FuzzyChoice
from ebl.tests.factories.factory_meta import FactoryMeta

from ebl.fragmentarium.domain.record import Record, RecordEntry, RecordType
from ebl.tests.factories.collections import TUPLE_FACTORY


class RecordEntryFactory(Factory):
    class Meta(FactoryMeta):
        model = RecordEntry

    user = Faker("last_name")
    type = FuzzyChoice(RecordType)
    date = Faker("iso8601")


class RecordFactory(Factory):
    class Meta(FactoryMeta):
        model = Record

    entries = List([SubFactory(RecordEntryFactory)], TUPLE_FACTORY)
