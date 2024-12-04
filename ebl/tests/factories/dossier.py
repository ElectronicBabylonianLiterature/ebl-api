import factory
from ebl.dossier.domain.dossier_record import DossierRecord
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.collections import TupleFactory
from ebl.common.domain.provenance import Provenance
from ebl.tests.factories.fragment import ScriptFactory


class DossierRecordFactory(factory.Factory):
    class Meta:
        model = DossierRecord

    id = factory.Faker("random_int", min=0, max=1000)
    name = factory.Faker("word")
    description = factory.Faker("sentence")
    is_approximate_date = factory.Faker("boolean")
    year_range_from = factory.Maybe("is_approximate_date", factory.Faker("year"), None)
    year_range_to = factory.Maybe(
        "is_approximate_date",
        factory.LazyAttribute(
            lambda obj: obj.year_range_from
            + factory.Faker("random_int").generate({"min": 1, "max": 50})
        ),
        None,
    )
    related_kings = factory.LazyAttribute(
        lambda _: [
            factory.Faker("random_int", min=1, max=100).generate()
            for _ in range(factory.Faker("random_int", min=0, max=5).generate())
        ]
    )
    provenance = factory.fuzzy.FuzzyChoice(set(Provenance) - {Provenance.STANDARD_TEXT})
    script = factory.SubFactory(ScriptFactory)
    references = factory.List(
        [factory.SubFactory(ReferenceFactory, with_document=True)], TupleFactory
    )
