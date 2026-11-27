from factory.base import Factory
from factory.declarations import LazyAttribute, Sequence, SubFactory
from factory.faker import Faker
from factory.fuzzy import FuzzyChoice
from ebl.tests.factories.factory_meta import FactoryMeta
from random import randint
from ebl.dossiers.domain.dossier_record import (
    DossierRecord,
)
from ebl.tests.factories.provenance import DEFAULT_NON_STANDARD_PROVENANCES
from ebl.tests.factories.fragment import ScriptFactory
from ebl.chronology.chronology import chronology
from ebl.tests.factories.bibliography import ReferenceFactory

APPROXIMATE_YEAR_FROM = randint(-2500, -400)


class DossierRecordFactory(Factory):
    class Meta(FactoryMeta):
        model = DossierRecord

    id = Sequence(lambda n: f"dossier-{n}")
    description = Faker("sentence")
    is_approximate_date = Faker("boolean")
    year_range_from = LazyAttribute(
        lambda obj: APPROXIMATE_YEAR_FROM if obj.is_approximate_date else None
    )
    year_range_to = LazyAttribute(
        lambda obj: (
            obj.year_range_from + randint(0, 500) if obj.is_approximate_date else None
        )
    )
    related_kings = LazyAttribute(
        lambda _: [chronology.kings[i].order_global for i in range(randint(0, 10))]
    )
    provenance = FuzzyChoice(DEFAULT_NON_STANDARD_PROVENANCES)
    script = SubFactory(ScriptFactory)
    references = LazyAttribute(
        lambda _: tuple(
            ReferenceFactory(with_document=True) for _ in range(randint(1, 5))
        )
    )
