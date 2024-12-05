import factory
from random import randint
from ebl.dossier.domain.dossier_record import (
    DossierRecord,
)
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.collections import TupleFactory
from ebl.common.domain.provenance import Provenance
from ebl.tests.factories.fragment import ScriptFactory
from ebl.chronology.chronology import chronology


class DossierRecordFactory(factory.Factory):
    class Meta:
        model = DossierRecord

    name = factory.Faker("word")
    description = factory.Faker("sentence")
    is_approximate_date = factory.Faker("boolean")
    year_range_from = factory.Maybe("is_approximate_date", randint(-2500, -400), None)
    year_range_to = factory.Maybe(
        "is_approximate_date",
        factory.LazyAttribute(lambda obj: obj.year_range_from + randint(0, 500)),
        None,
    )
    related_kings = factory.LazyAttribute(
        lambda _: [chronology.kings[i].order_global for i in range(randint(0, 100))]
    )
    provenance = factory.fuzzy.FuzzyChoice(set(Provenance) - {Provenance.STANDARD_TEXT})
    script = factory.SubFactory(ScriptFactory)
    references = factory.List(
        [factory.SubFactory(ReferenceFactory, with_document=True)], TupleFactory
    )
