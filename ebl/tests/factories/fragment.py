import random
from typing import Sequence as TypingSequence

import factory.fuzzy
from factory.declarations import Iterator, List, Sequence, SubFactory
from factory.faker import Faker
from factory.helpers import make_factory

from ebl.common.domain.accession import Accession
from ebl.common.domain.project import ResearchProject
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.domain.museum import Museum
from ebl.tests.factories.archaeology import ArchaeologyFactory
from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.fragmentarium.domain.fragment import (
    Fragment,
    Genre,
    Introduction,
    Notes,
    UncuratedReference,
)

from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncoding
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.text import Text
from ebl.fragmentarium.domain.record import Record, RecordEntry, RecordType
from ebl.tests.factories.colophon import ColophonFactory
from ebl.tests.factories.fragment_metadata_factories import (
    AcquisitionFactory,
    DateFactory,
    DayFactory,
    ExternalNumbersFactory,
    FragmentDossierReferenceFactory,
    JoinFactory,
    MonthFactory,
    ScriptFactory,
    YearFactory,
    create_date_king,
)
from ebl.tests.factories.lemmatized_fragment_text import LEMMATIZED_FRAGMENT_TEXT
from ebl.tests.factories.transliterated_fragment_text import (
    TRANSLITERATED_FRAGMENT_TEXT,
)

__all__ = [
    "AcquisitionFactory",
    "DateFactory",
    "DayFactory",
    "ExternalNumbersFactory",
    "FragmentDossierReferenceFactory",
    "FragmentFactory",
    "InterestingFragmentFactory",
    "JoinFactory",
    "LemmatizedFragmentFactory",
    "MonthFactory",
    "ScriptFactory",
    "TransliteratedFragmentFactory",
    "YearFactory",
    "create_date_king",
]

GENRE_CHOICES = [
    (
        Genre(["ARCHIVAL", "Administrative", "Lists", "One Entry"], False),
        Genre(["CANONICAL", "Catalogues"], False),
    ),
    (Genre(["ARCHIVAL", "Administrative", "Lists", "One Entry"], False),),
]
DEFAULT_PROJECTS = (
    ResearchProject.CAIC,
    ResearchProject.ALU_GENEVA,
    ResearchProject.AMPS,
    ResearchProject.RECC,
)
DEFAULT_AUTHORIZED_SCOPES: list[Scope] = []


FragmentFactory = make_factory(
    Fragment,
    number=Sequence(lambda n: MuseumNumber("X", str(n))),
    accession=Sequence(lambda n: Accession("A", str(n))),
    museum=factory.fuzzy.FuzzyChoice([m for m in Museum if m != Museum.UNKNOWN]),
    collection=Faker("word"),
    publication=Faker("sentence"),
    acquisition=SubFactory(AcquisitionFactory),
    description=Faker("text"),
    legacy_script=Iterator(["NA", "NB"]),
    script=SubFactory(ScriptFactory),
    date=SubFactory(DateFactory),
    dates_in_text=List([SubFactory(DateFactory) for _ in range(random.randint(0, 4))]),
    folios=Folios((Folio("WGL", "1"), Folio("ARG", "1"))),
    genres=Iterator(GENRE_CHOICES),
    authorized_scopes=DEFAULT_AUTHORIZED_SCOPES,
    introduction=Introduction("text", (StringPart("text"),)),
    notes=Notes("notes", (StringPart("notes"),)),
    external_numbers=SubFactory(ExternalNumbersFactory),
    projects=DEFAULT_PROJECTS,
    archaeology=SubFactory(ArchaeologyFactory),
    colophon=SubFactory(ColophonFactory),
    ocred_signs="ABZ10 X",
    dossiers=List(
        [
            SubFactory(FragmentDossierReferenceFactory)
            for _ in range(random.randint(0, 4))
        ]
    ),
    named_entities=(),
)


INTERESTING_JOINS: TypingSequence[str] = ()
TRANSLITERATED_SIGNS = (
    "X BA KU ABZ075 ABZ207a\\u002F207b\\u0020X ABZ377n1/KU ABZ377n1 ABZ411\n"
    "MI DIŠ UD ŠU\n"
    "KI DU ABZ411 BA MA TI\n"
    "X MU TA MA UD\n"
    "ŠU/|BI×IS|"
)
TRANSLITERATED_LINE_TO_VEC = (
    (
        LineToVecEncoding.TEXT_LINE,
        LineToVecEncoding.TEXT_LINE,
        LineToVecEncoding.TEXT_LINE,
        LineToVecEncoding.TEXT_LINE,
        LineToVecEncoding.TEXT_LINE,
        LineToVecEncoding.SINGLE_RULING,
    ),
)


InterestingFragmentFactory = make_factory(
    Fragment,
    FACTORY_CLASS=FragmentFactory,
    collection="Kuyunjik",
    publication="",
    joins=INTERESTING_JOINS,
    text=Text(),
    uncurated_references=(
        UncuratedReference("7(0)"),
        UncuratedReference("CAD 51", (34, 56)),
        UncuratedReference("7(1)"),
    ),
    references=(),
    notes=Notes(),
)
InterestingFragmentFactory.__name__ = "InterestingFragmentFactory"

TransliteratedFragmentFactory = make_factory(
    Fragment,
    FACTORY_CLASS=FragmentFactory,
    text=TRANSLITERATED_FRAGMENT_TEXT,
    signs=TRANSLITERATED_SIGNS,
    ocred_signs="ABZ10 X",
    folios=Folios((Folio("WGL", "3"), Folio("ARG", "3"))),
    record=Record((RecordEntry("test", RecordType.TRANSLITERATION),)),
    line_to_vec=TRANSLITERATED_LINE_TO_VEC,
)
TransliteratedFragmentFactory.__name__ = "TransliteratedFragmentFactory"

LemmatizedFragmentFactory = make_factory(
    Fragment,
    FACTORY_CLASS=TransliteratedFragmentFactory,
    text=LEMMATIZED_FRAGMENT_TEXT,
)
LemmatizedFragmentFactory.__name__ = "LemmatizedFragmentFactory"
