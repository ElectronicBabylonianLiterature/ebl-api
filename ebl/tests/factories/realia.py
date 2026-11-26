from factory.base import Factory
from factory.declarations import LazyAttribute, Sequence, SubFactory
from factory.faker import Faker
from ebl.tests.factories.factory_meta import FactoryMeta

from ebl.realia.domain.realia_entry import (
    AfoCrossReference,
    AfoRegisterEntry,
    CrossReference,
    RealiaEntry,
    ReallexikonEntry,
)
from ebl.tests.factories.bibliography import ReferenceFactory

REALIA_TYPES = ("Personal names", "Geographical names", "Divine names")


class CrossReferenceFactory(Factory):
    class Meta(FactoryMeta):
        model = CrossReference

    id = Sequence(lambda n: f"realia_{n:06d}")
    lemma = Sequence(lambda n: f"lemma-{n}")


class AfoCrossReferenceFactory(Factory):
    class Meta(FactoryMeta):
        model = AfoCrossReference

    id = Sequence(lambda n: f"realia_{n:06d}")
    lemma = Sequence(lambda n: f"lemma-{n}")
    afo_volume = Sequence(lambda n: f"AfO {n}")
    page = Sequence(str)


class AfoRegisterEntryFactory(Factory):
    class Meta(FactoryMeta):
        model = AfoRegisterEntry

    main_word = Faker("word")
    note = Faker("sentence")
    afo = Sequence(lambda n: f"AfO {n}")
    reference = Sequence(lambda n: f"p. {n}")
    cross_reference = Faker("word")
    afo_volume = Sequence(lambda n: f"AfO {n}")
    page = Sequence(str)
    cross_references = LazyAttribute(lambda _: (AfoCrossReferenceFactory.build(),))


class ReallexikonEntryFactory(Factory):
    class Meta(FactoryMeta):
        model = ReallexikonEntry

    id = Sequence(lambda n: f"RlA-{n}")
    title = Faker("sentence")
    reference = SubFactory(ReferenceFactory, with_document=True)


class RealiaEntryFactory(Factory):
    class Meta(FactoryMeta):
        model = RealiaEntry

    id = Sequence(lambda n: f"Realia {n}")
    realia_id = Sequence(lambda n: f"realia_{n:06d}")
    related_terms = LazyAttribute(lambda _: tuple(f"term-{i}" for i in range(2)))
    type = LazyAttribute(lambda _: (REALIA_TYPES[0], REALIA_TYPES[1]))
    afo_register = LazyAttribute(
        lambda _: tuple(AfoRegisterEntryFactory.build() for _ in range(2))
    )
    references = LazyAttribute(
        lambda _: tuple(ReferenceFactory(with_document=True) for _ in range(2))
    )
    wikidata_id = LazyAttribute(lambda _: tuple(f"Q{n}" for n in range(1, 3)))
    reallexikon = LazyAttribute(
        lambda _: tuple(ReallexikonEntryFactory.build() for _ in range(2))
    )
    cross_references = LazyAttribute(lambda _: (CrossReferenceFactory.build(),))
    afo_cross_references = LazyAttribute(lambda _: (AfoCrossReferenceFactory.build(),))
