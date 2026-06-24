import factory

from ebl.realia.domain.realia_entry import (
    AfoRegisterEntry,
    RealiaEntry,
    ReallexikonEntry,
)
from ebl.tests.factories.bibliography import ReferenceFactory

REALIA_TYPES = ("Personal names", "Geographical names", "Divine names")


class AfoRegisterEntryFactory(factory.Factory):
    class Meta:
        model = AfoRegisterEntry

    main_word = factory.Faker("word")
    note = factory.Faker("sentence")
    afo = factory.Sequence(lambda n: f"AfO {n}")
    reference = factory.Sequence(lambda n: f"p. {n}")
    cross_reference = factory.Faker("word")


class ReallexikonEntryFactory(factory.Factory):
    class Meta:
        model = ReallexikonEntry

    id = factory.Sequence(lambda n: f"RlA-{n}")
    title = factory.Faker("sentence")
    reference = factory.SubFactory(ReferenceFactory, with_document=True)
    content = factory.Faker("paragraph")


class RealiaEntryFactory(factory.Factory):
    class Meta:
        model = RealiaEntry

    id = factory.Sequence(lambda n: f"Realia {n}")
    related_terms = factory.LazyAttribute(
        lambda _: tuple(f"term-{i}" for i in range(2))
    )
    type = factory.LazyAttribute(lambda _: (REALIA_TYPES[0], REALIA_TYPES[1]))
    afo_register = factory.LazyAttribute(
        lambda _: tuple(AfoRegisterEntryFactory.build() for _ in range(2))
    )
    references = factory.LazyAttribute(
        lambda _: tuple(ReferenceFactory(with_document=True) for _ in range(2))
    )
    wikidata_id = factory.LazyAttribute(lambda _: tuple(f"Q{n}" for n in range(1, 3)))
    reallexikon = factory.LazyAttribute(
        lambda _: tuple(ReallexikonEntryFactory.build() for _ in range(2))
    )
