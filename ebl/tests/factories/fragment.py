from typing import Sequence
import pydash
import factory.fuzzy
import random
from ebl.common.domain.accession import Accession
from ebl.common.domain.period import Period, PeriodModifier
from ebl.common.domain.project import ResearchProject
from ebl.fragmentarium.domain.museum import Museum
from ebl.corpus.domain.chapter import Stage
from ebl.tests.factories.archaeology import ArchaeologyFactory
from ebl.tests.factories.collections import TupleFactory
from ebl.transliteration.domain.text_id import TextId
from ebl.dictionary.domain.word import WordId
from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.fragmentarium.domain.fragment import (
    Acquisition,
    DossierReference,
    Fragment,
    Genre,
    Introduction,
    Notes,
    Script,
    UncuratedReference,
)

from ebl.fragmentarium.domain.fragment_external_numbers import ExternalNumbers
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncoding
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (
    ColumnAtLine,
    CompositeAtLine,
    DiscourseAtLine,
    DivisionAtLine,
    HeadingAtLine,
    ObjectAtLine,
    SealAtLine,
    SurfaceAtLine,
)
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.dollar_line import (
    ImageDollarLine,
    LooseDollarLine,
    RulingDollarLine,
    ScopeContainer,
    SealDollarLine,
    StateDollarLine,
)
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.genre import Genre as CorpusGenre
from ebl.transliteration.domain.labels import ColumnLabel, ObjectLabel, SurfaceLabel
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import EmphasisPart, LanguagePart, StringPart
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import (
    ChapterName,
    Labels,
    ParallelComposition,
    ParallelFragment,
    ParallelText,
)
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Divider,
    Logogram,
    Number,
    Reading,
)
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Column,
    CommentaryProtocol,
    Joiner,
    LanguageShift,
    WordOmitted,
    Tabulation,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import InWordNewline, Word
from ebl.fragmentarium.domain.joins import Join
from ebl.fragmentarium.domain.record import Record, RecordEntry, RecordType
from ebl.fragmentarium.domain.date import (
    Date,
    Year,
    Month,
    Day,
    DateKing,
    DateKingSchema,
    Ur3Calendar,
)
from ebl.chronology.chronology import chronology, King
from ebl.tests.factories.colophon import ColophonFactory


class JoinFactory(factory.Factory):
    class Meta:
        model = Join

    museum_number = factory.Sequence(
        lambda n: MuseumNumber("M", str(n)) if pydash.is_odd(n) else None
    )
    is_checked = factory.Faker("boolean")
    is_envelope = factory.Faker("boolean")
    joined_by = factory.Faker("word")
    date = factory.Faker("date")
    note = factory.Faker("sentence")
    legacy_data = factory.Faker("sentence")
    is_in_fragmentarium = factory.Faker("boolean")


class ScriptFactory(factory.Factory):
    class Meta:
        model = Script

    period = factory.fuzzy.FuzzyChoice(set(Period) - {Period.NONE})
    period_modifier = factory.fuzzy.FuzzyChoice(set(PeriodModifier))
    uncertain = factory.Faker("boolean")


class YearFactory(factory.Factory):
    class Meta:
        model = Year

    value = factory.Faker("word")
    is_broken = factory.Faker("boolean")
    is_uncertain = factory.Faker("boolean")


class MonthFactory(factory.Factory):
    class Meta:
        model = Month

    value = factory.Faker("word")
    is_broken = factory.Faker("boolean")
    is_uncertain = factory.Faker("boolean")
    is_intercalary = factory.Faker("boolean")


class DayFactory(factory.Factory):
    class Meta:
        model = Day

    value = factory.Faker("word")
    is_broken = factory.Faker("boolean")
    is_uncertain = factory.Faker("boolean")


def create_date_king(king: King) -> DateKing:
    return DateKingSchema().load(
        {
            "orderGlobal": king.order_global,
            "isBroken": random.choice([True, False]),
            "isUncertain": random.choice([True, False]),
        }
    )


class DateFactory(factory.Factory):
    class Meta:
        model = Date

    year = factory.SubFactory(YearFactory)
    month = factory.SubFactory(MonthFactory)
    day = factory.SubFactory(DayFactory)
    king = factory.Iterator(
        chronology.kings, getter=lambda king: create_date_king(king)
    )
    is_seleucid_era = factory.Faker("boolean")
    ur3_calendar = factory.Iterator(Ur3Calendar)


class ExternalNumbersFactory(factory.Factory):
    class Meta:
        model = ExternalNumbers

    cdli_number = factory.Sequence(lambda n: f"cdli-{n}")
    bm_id_number = factory.Sequence(lambda n: f"bmId-{n}")
    archibab_number = factory.Sequence(lambda n: f"archibab-{n}")
    bdtns_number = factory.Sequence(lambda n: f"bdtns-{n}")
    rsti_number = factory.Sequence(lambda n: f"rsti-{n}")
    chicago_isac_number = factory.Sequence(lambda n: f"chicago-isac-number-{n}")
    ur_online_number = factory.Sequence(lambda n: f"ur-online-{n}")
    hilprecht_jena_number = factory.Sequence(lambda n: f"hilprecht-jena-{n}")
    hilprecht_heidelberg_number = factory.Sequence(
        lambda n: f"hilprecht-heidelberg-{n}"
    )
    metropolitan_number = factory.Sequence(lambda n: f"metropolitan-number-{n}")
    pierpont_morgan_number = factory.Sequence(lambda n: f"pierpont-morgan-number-{n}")
    louvre_number = factory.Sequence(lambda n: f"louvre-number-{n}")
    dublin_tcd_number = factory.Sequence(lambda n: f"dublin-tcd-number-{n}")
    cambridge_maa_number = factory.Sequence(lambda n: f"cambridge-maa-number-{n}")
    ashmolean_number = factory.Sequence(lambda n: f"ashmolean-number-{n}")
    alalah_hpm_number = factory.Sequence(lambda n: f"alalah-hpm-number-{n}")
    australianinstituteofarchaeology_number = factory.Sequence(
        lambda n: f"australianinstituteofarchaeology-number-{n}"
    )
    philadelphia_number = factory.Sequence(lambda n: f"philadelphia-number-{n}")
    yale_peabody_number = factory.Sequence(lambda n: f"yale-peabody-number-{n}")
    achemenet_number = factory.Sequence(lambda n: f"achemenet-number-{n}")
    nabucco_number = factory.Sequence(lambda n: f"nabucco-number-{n}")
    digitale_keilschrift_bibliothek_number = factory.Sequence(
        lambda n: f"digitale-keilschrift-bibliothek-{n}"
    )
    oracc_numbers = factory.List(
        [factory.Sequence(lambda n: f"oracc-number-{n}")], TupleFactory
    )
    seal_numbers = factory.List(
        [factory.Sequence(lambda n: f"seal_number-{n}")], TupleFactory
    )


class FragmentDossierReferenceFactory(factory.Factory):
    class Meta:
        model = DossierReference

    dossierId = factory.Faker("word")
    isUncertain = factory.Faker("boolean")


class AcquisitionFactory(factory.Factory):
    class Meta:
        model = Acquisition

    description = factory.Faker("sentence")
    supplier = factory.Faker("word")
    date = 0


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
    authorized_scopes = []
    introduction = Introduction("text", (StringPart("text"),))
    notes = Notes("notes", (StringPart("notes"),))
    external_numbers = factory.SubFactory(ExternalNumbersFactory)
    projects = (ResearchProject.CAIC, ResearchProject.ALU_GENEVA, ResearchProject.AMPS)
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
    text = Text(
        (
            TextLine.of_iterable(
                LineNumber(1, True),
                (
                    Word.of([UnidentifiedSign.of()]),
                    Word.of(
                        [
                            Logogram.of_name(
                                "BA",
                                surrogate=[
                                    Reading.of_name("ku"),
                                    Joiner.hyphen(),
                                    Reading.of_name("u", 4),
                                ],
                            )
                        ]
                    ),
                    Column.of(),
                    WordOmitted.of(),
                    Tabulation.of(),
                    Word.of(
                        [
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            Joiner.hyphen(),
                            Reading.of_name("ku"),
                            BrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name("nu"),
                            Joiner.hyphen(),
                            Reading.of_name("ši"),
                        ]
                    ),
                    Variant.of(Divider.of(":"), Reading.of_name("ku")),
                    Word.of(
                        [
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                        ]
                    ),
                    Column.of(2),
                    Divider.of(":", ("@v",), (Flag.DAMAGE,)),
                    CommentaryProtocol.of("!qt"),
                    Word.of([Number.of_name("10", flags=[Flag.DAMAGE])]),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(2, True),
                (
                    Word.of(
                        [
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                        ]
                    ),
                    Word.of([Logogram.of_name("GI", 6)]),
                    Word.of([Reading.of_name("ana")]),
                    Word.of(
                        [
                            Reading.of_name("u", 4),
                            Joiner.hyphen(),
                            Reading.of(
                                (
                                    ValueToken.of("š"),
                                    BrokenAway.open(),
                                    ValueToken.of("u"),
                                )
                            ),
                        ]
                    ),
                    Word.of([UnknownNumberOfSigns.of(), BrokenAway.close()]),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(3, True),
                (
                    Word.of([BrokenAway.open(), UnknownNumberOfSigns.of()]),
                    Word.of(
                        [
                            Reading.of(
                                (
                                    ValueToken.of("k"),
                                    BrokenAway.close(),
                                    ValueToken.of("i"),
                                )
                            ),
                            Joiner.hyphen(),
                            Reading.of_name("du"),
                        ]
                    ),
                    Word.of([Reading.of_name("u")]),
                    Word.of(
                        [
                            Reading.of_name("ba"),
                            Joiner.hyphen(),
                            Reading.of_name("ma"),
                            Joiner.hyphen(),
                            Reading.of(
                                (
                                    ValueToken.of("t"),
                                    BrokenAway.open(),
                                    ValueToken.of("i"),
                                )
                            ),
                        ]
                    ),
                    Word.of([UnknownNumberOfSigns.of(), BrokenAway.close()]),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(6, True),
                (
                    Word.of(
                        [
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                        ]
                    ),
                    Word.of([UnclearSign.of([Flag.DAMAGE])]),
                    Word.of([Reading.of_name("mu")]),
                    Word.of(
                        [
                            Reading.of_name("ta"),
                            Joiner.hyphen(),
                            Reading.of_name("ma"),
                            InWordNewline.of(),
                            Joiner.hyphen(),
                            Reading.of_name("tu", 2),
                        ]
                    ),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(7, True),
                (
                    Word.of(
                        [
                            Variant.of(
                                Reading.of_name("šu"), CompoundGrapheme.of(["BI×IS"])
                            )
                        ]
                    ),
                    LanguageShift.normalized_akkadian(),
                    AkkadianWord.of([ValueToken.of("kur")]),
                ),
            ),
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Surface.OBVERSE, ""),
                atf.State.MISSING,
                None,
            ),
            ImageDollarLine("1", None, "numbered diagram of triangle"),
            RulingDollarLine(atf.Ruling.SINGLE),
            LooseDollarLine("this is a loose line"),
            SealDollarLine(1),
            SealAtLine(1),
            HeadingAtLine(1),
            ColumnAtLine(ColumnLabel([atf.Status.COLLATION], 1)),
            SurfaceAtLine(
                SurfaceLabel([atf.Status.COLLATION], atf.Surface.SURFACE, "stone wig")
            ),
            ObjectAtLine(
                ObjectLabel([atf.Status.COLLATION], atf.Object.OBJECT, "stone wig")
            ),
            DiscourseAtLine(atf.Discourse.DATE),
            DivisionAtLine("paragraph", 5),
            CompositeAtLine(atf.Composite.DIV, "part", 1),
            NoteLine(
                (
                    StringPart("a note "),
                    EmphasisPart("italic"),
                    LanguagePart.of_transliteration(
                        Language.AKKADIAN, (Word.of([Reading.of_name("bu")]),)
                    ),
                )
            ),
            ParallelComposition(False, "my name", LineNumber(1)),
            ParallelText(
                True,
                TextId(CorpusGenre.LITERATURE, 1, 1),
                ChapterName(Stage.OLD_BABYLONIAN, "", "my name"),
                LineNumber(1),
                False,
            ),
            ParallelFragment(
                False, MuseumNumber.of("K.1"), True, Labels(), LineNumber(1), False
            ),
        )
    )
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
    text = Text(
        (
            TextLine.of_iterable(
                LineNumber(1, True),
                (
                    Word.of([UnidentifiedSign.of()]),
                    Word.of(
                        [
                            Logogram.of_name(
                                "BA",
                                surrogate=[
                                    Reading.of_name("ku"),
                                    Joiner.hyphen(),
                                    Reading.of_name("u", 4),
                                ],
                            )
                        ]
                    ),
                    Column.of(),
                    WordOmitted.of(),
                    Tabulation.of(),
                    Word.of(
                        [
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            Joiner.hyphen(),
                            Reading.of_name("ku"),
                            BrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name("nu"),
                            Joiner.hyphen(),
                            Reading.of_name("ši"),
                        ]
                    ),
                    Variant.of(Divider.of(":"), Reading.of_name("ku")),
                    Word.of(
                        [
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                        ]
                    ),
                    Column.of(2),
                    Divider.of(":", ("@v",), (Flag.DAMAGE,)),
                    CommentaryProtocol.of("!qt"),
                    Word.of([Number.of_name("10", flags=[Flag.DAMAGE])]),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(2, True),
                (
                    Word.of([BrokenAway.open(), UnknownNumberOfSigns.of()]),
                    Word.of(
                        [Logogram.of_name("GI", 6)], unique_lemma=(WordId("ginâ I"),)
                    ),
                    Word.of([Reading.of_name("ana")], unique_lemma=(WordId("ana I"),)),
                    Word.of(
                        [
                            Reading.of_name("u₄"),
                            Joiner.hyphen(),
                            Reading.of_name("š[u"),
                        ],
                        unique_lemma=(WordId("ūsu I"),),
                    ),
                    Word.of([UnknownNumberOfSigns.of(), BrokenAway.close()]),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(3, True),
                (
                    Word.of([BrokenAway.open(), UnknownNumberOfSigns.of()]),
                    Word.of(
                        unique_lemma=(WordId("kīdu I"),),
                        parts=[
                            Reading.of(
                                (
                                    ValueToken.of("k"),
                                    BrokenAway.close(),
                                    ValueToken.of("i"),
                                )
                            ),
                            Joiner.hyphen(),
                            Reading.of_name("du"),
                        ],
                    ),
                    Word.of(
                        unique_lemma=(WordId("u I"),), parts=[Reading.of_name("u")]
                    ),
                    Word.of(
                        unique_lemma=(WordId("bamātu I"),),
                        parts=[
                            Reading.of_name("ba"),
                            Joiner.hyphen(),
                            Reading.of_name("ma"),
                            Joiner.hyphen(),
                            Reading.of(
                                (
                                    ValueToken.of("t"),
                                    BrokenAway.open(),
                                    ValueToken.of("i"),
                                )
                            ),
                        ],
                    ),
                    Word.of([UnknownNumberOfSigns.of(), BrokenAway.close()]),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(6, True),
                (
                    Word.of(
                        [
                            BrokenAway.open(),
                            UnknownNumberOfSigns.of(),
                            BrokenAway.close(),
                        ]
                    ),
                    Word.of([UnclearSign.of([Flag.DAMAGE])]),
                    Word.of(
                        unique_lemma=(WordId("mu I"),), parts=[Reading.of_name("mu")]
                    ),
                    Word.of(
                        unique_lemma=(WordId("tamalāku I"),),
                        parts=[
                            Reading.of_name("ta"),
                            Joiner.hyphen(),
                            Reading.of_name("ma"),
                            InWordNewline.of(),
                            Joiner.hyphen(),
                            Reading.of_name("tu", 2),
                        ],
                    ),
                ),
            ),
            TextLine.of_iterable(
                LineNumber(7, True),
                (
                    Word.of(
                        [
                            Variant.of(
                                Reading.of_name("šu"), CompoundGrapheme.of(["BI×IS"])
                            )
                        ]
                    ),
                    LanguageShift.normalized_akkadian(),
                    AkkadianWord.of(
                        [ValueToken.of("kur")], unique_lemma=(WordId("normalized I"),)
                    ),
                ),
            ),
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Surface.OBVERSE, ""),
                atf.State.MISSING,
                None,
            ),
            ImageDollarLine("1", None, "numbered diagram of triangle"),
            RulingDollarLine(atf.Ruling.SINGLE),
            LooseDollarLine("this is a loose line"),
            SealDollarLine(1),
            SealAtLine(1),
            HeadingAtLine(1),
            ColumnAtLine(ColumnLabel([atf.Status.COLLATION], 1)),
            SurfaceAtLine(
                SurfaceLabel([atf.Status.COLLATION], atf.Surface.SURFACE, "stone wig")
            ),
            ObjectAtLine(
                ObjectLabel([atf.Status.COLLATION], atf.Object.OBJECT, "stone wig")
            ),
            DiscourseAtLine(atf.Discourse.DATE),
            DivisionAtLine("paragraph", 5),
            CompositeAtLine(atf.Composite.DIV, "part", 1),
            NoteLine(
                (
                    StringPart("a note "),
                    EmphasisPart("italic"),
                    LanguagePart.of_transliteration(
                        Language.AKKADIAN, (Word.of([Reading.of_name("bu")]),)
                    ),
                )
            ),
            ParallelComposition(False, "my name", LineNumber(1)),
            ParallelText(
                True,
                TextId(CorpusGenre.LITERATURE, 1, 1),
                ChapterName(Stage.OLD_BABYLONIAN, "", "my name"),
                LineNumber(1),
                False,
            ),
            ParallelFragment(
                False, MuseumNumber.of("K.1"), True, Labels(), LineNumber(1), False
            ),
        )
    )
