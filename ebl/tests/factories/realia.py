from factory.declarations import LazyAttribute, SelfAttribute, Sequence, SubFactory
from factory.faker import Faker
from factory.helpers import make_factory

from ebl.realia.domain.realia_entry import (
    AfoCrossReference,
    AfoRegisterEntry,
    CrossReference,
    EblRealiaEntry,
    RealiaEntry,
    ReallexikonEntry,
)
from ebl.tests.factories.bibliography import ReferenceFactory

REALIA_TYPES = ("Personal names", "Geographical names", "Divine names")


CrossReferenceFactory = make_factory(
    CrossReference,
    id=Sequence(lambda n: f"realia_{n:06d}"),
    lemma=Sequence(lambda n: f"lemma-{n}"),
)

AfoCrossReferenceFactory = make_factory(
    AfoCrossReference,
    id=Sequence(lambda n: f"realia_{n:06d}"),
    lemma=Sequence(lambda n: f"lemma-{n}"),
    afo_volume=Sequence(lambda n: f"AfO {n}"),
    page=Sequence(str),
)

AfoRegisterEntryFactory = make_factory(
    AfoRegisterEntry,
    main_word=Faker("word"),
    note=Faker("sentence"),
    afo=Sequence(lambda n: f"AfO {n}"),
    reference=Sequence(lambda n: f"p. {n}"),
    cross_reference=Faker("word"),
    afo_volume=Sequence(lambda n: f"AfO {n}"),
    page=Sequence(str),
    cross_references=LazyAttribute(lambda _: (AfoCrossReferenceFactory.build(),)),
)

ReallexikonEntryFactory = make_factory(
    ReallexikonEntry,
    id=Sequence(lambda n: f"RlA-{n}"),
    title=Faker("sentence"),
    reference=SubFactory(ReferenceFactory, with_document=True),
)

EblRealiaEntryFactory = make_factory(
    EblRealiaEntry,
    id=Sequence(lambda n: f"MÚL-{n}"),
    transliteration=SelfAttribute("id"),
    normalisation=Faker("word"),
    translation=Faker("sentence"),
    identification=Sequence(lambda n: f"star {n}"),
    part_of_speech="CN",
    wikidata_id=Sequence(lambda n: (f"Q{n}",)),
    reference=SubFactory(ReferenceFactory, with_document=True),
    remarks=Faker("sentence"),
)

RealiaEntryFactory = make_factory(
    RealiaEntry,
    id=Sequence(lambda n: f"Realia {n}"),
    realia_id=Sequence(lambda n: f"realia_{n:06d}"),
    related_terms=LazyAttribute(lambda _: tuple(f"term-{i}" for i in range(2))),
    type=LazyAttribute(lambda _: (REALIA_TYPES[0], REALIA_TYPES[1])),
    afo_register=LazyAttribute(
        lambda _: tuple(AfoRegisterEntryFactory.build() for _ in range(2))
    ),
    references=LazyAttribute(
        lambda _: tuple(ReferenceFactory(with_document=True) for _ in range(2))
    ),
    wikidata_id=LazyAttribute(lambda _: tuple(f"Q{n}" for n in range(1, 3))),
    reallexikon=LazyAttribute(
        lambda _: tuple(ReallexikonEntryFactory.build() for _ in range(2))
    ),
    cross_references=LazyAttribute(lambda _: (CrossReferenceFactory.build(),)),
    afo_cross_references=LazyAttribute(lambda _: (AfoCrossReferenceFactory.build(),)),
    reference_type=("RlA", "AfO", "eBL"),
    ebl_realia=LazyAttribute(lambda _: (EblRealiaEntryFactory.build(),)),
)
