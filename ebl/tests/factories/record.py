import factory  # pyre-ignore.fuzzy  # pyre-ignore  # pyre-ignore

from ebl.fragmentarium.domain.record import Record, RecordEntry, RecordType
from ebl.tests.factories.collections import TupleFactory


class RecordEntryFactory(factory.Factory):  # pyre-ignore[11]
    class Meta:
        model = RecordEntry

    user = factory.Faker("last_name")
    type = factory.fuzzy.FuzzyChoice(RecordType)
    date = factory.Faker("iso8601")


class RecordFactory(factory.Factory):  # pyre-ignore[11]
    class Meta:
        model = Record

    entries = factory.List([factory.SubFactory(RecordEntryFactory)], TupleFactory)
