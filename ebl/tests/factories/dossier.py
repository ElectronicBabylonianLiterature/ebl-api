import factory
from random import randint
from ebl.dossiers.domain.dossier_record import (
    DossierRecord,
)
from ebl.tests.factories.provenance import DEFAULT_NON_STANDARD_PROVENANCES
from ebl.tests.factories.fragment import ScriptFactory
from ebl.chronology.chronology import chronology
from ebl.tests.factories.bibliography import ReferenceFactory


class DossierRecordFactory(factory.Factory):
    class Meta:
        model = DossierRecord

    id = factory.Sequence(lambda index: f"dossier_{index}")
    description = factory.Faker("sentence")
    is_approximate_date = factory.Faker("boolean")
    year_range_from = factory.Maybe("is_approximate_date", randint(-2500, -400), None)
    year_range_to = factory.Maybe(
        "is_approximate_date",
        factory.LazyAttribute(lambda obj: obj.year_range_from + randint(0, 500)),
        None,
    )
    related_kings = factory.LazyAttribute(
        lambda _: [chronology.kings[i].order_global for i in range(randint(0, 10))]
    )
    provenance = factory.fuzzy.FuzzyChoice(DEFAULT_NON_STANDARD_PROVENANCES)
    script = factory.SubFactory(ScriptFactory)
    references = factory.LazyAttribute(
        lambda _: tuple(
            ReferenceFactory(with_document=True) for _ in range(randint(1, 5))
        )
    )
