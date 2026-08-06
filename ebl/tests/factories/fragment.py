from typing import Sequence
import factory.fuzzy
import random
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


class FragmentFactory(factory.Factory):
    class Meta:
        model = Fragment

    number = factory.Sequence(lambda n: MuseumNumber("X", str(n)))
    accession = factory.Sequence(lambda n: Accession("A", str(n)))
    museum = factory.fuzzy.FuzzyChoice([m for m in Museum if m != Museum.UNKNOWN])
    collection = factory.Faker("word")
    publication = factory.Faker("sentence")
    acquisition = factory.SubFactory(AcquisitionFactory)
    description = factory.Faker("text")
    legacy_script = factory.Iterator(["NA", "NB"])
    script = factory.SubFactory(ScriptFactory)
    date = factory.SubFactory(DateFactory)
    dates_in_text = factory.List(
        [factory.SubFactory(DateFactory) for _ in range(random.randint(0, 4))]
    )
    folios = Folios((Folio("WGL", "1"), Folio("ARG", "1")))
    genres = factory.Iterator(
        [
            (
                Genre(["ARCHIVAL", "Administrative", "Lists", "One Entry"], False),
                Genre(["CANONICAL", "Catalogues"], False),
            ),
            (Genre(["ARCHIVAL", "Administrative", "Lists", "One Entry"], False),),
        ]
    )
    authorized_scopes: list[Scope] = []
    introduction = Introduction("text", (StringPart("text"),))
    notes = Notes("notes", (StringPart("notes"),))
    external_numbers = factory.SubFactory(ExternalNumbersFactory)
    projects = (
        ResearchProject.CAIC,
        ResearchProject.ALU_GENEVA,
        ResearchProject.AMPS,
        ResearchProject.RECC,
    )
    archaeology = factory.SubFactory(ArchaeologyFactory)
    colophon = factory.SubFactory(ColophonFactory)
    ocred_signs = "ABZ10 X"
    dossiers = factory.List(
        [
            factory.SubFactory(FragmentDossierReferenceFactory)
            for _ in range(random.randint(0, 4))
        ]
    )
    named_entities = ()


class InterestingFragmentFactory(FragmentFactory):
    collection = "Kuyunjik"  # pyre-ignore[15]
    publication = ""  # pyre-ignore[15]
    joins: Sequence[str] = ()
    text = Text()
    uncurated_references = (
        UncuratedReference("7(0)"),
        UncuratedReference("CAD 51", (34, 56)),
        UncuratedReference("7(1)"),
    )
    references = ()
    notes = Notes()


class TransliteratedFragmentFactory(FragmentFactory):
    text = TRANSLITERATED_FRAGMENT_TEXT
    signs = (
        "X BA KU ABZ075 ABZ207a\\u002F207b\\u0020X ABZ377n1/KU ABZ377n1 ABZ411\n"
        "MI DIŠ UD ŠU\n"
        "KI DU ABZ411 BA MA TI\n"
        "X MU TA MA UD\n"
        "ŠU/|BI×IS|"
    )
    ocred_signs = "ABZ10 X"
    folios = Folios((Folio("WGL", "3"), Folio("ARG", "3")))
    record = Record((RecordEntry("test", RecordType.TRANSLITERATION),))
    line_to_vec = (
        (
            LineToVecEncoding.TEXT_LINE,
            LineToVecEncoding.TEXT_LINE,
            LineToVecEncoding.TEXT_LINE,
            LineToVecEncoding.TEXT_LINE,
            LineToVecEncoding.TEXT_LINE,
            LineToVecEncoding.SINGLE_RULING,
        ),
    )


class LemmatizedFragmentFactory(TransliteratedFragmentFactory):
    text = LEMMATIZED_FRAGMENT_TEXT
