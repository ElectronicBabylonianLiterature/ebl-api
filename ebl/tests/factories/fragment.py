from typing import Sequence

import factory  # pyre-ignore

from ebl.dictionary.domain.word import WordId
from ebl.fragmentarium.application.matches.create_line_to_vec import LineToVecEncoding
from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.fragmentarium.domain.fragment import Fragment, UncuratedReference, Genre
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.record import RecordFactory
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (
    SealAtLine,
    HeadingAtLine,
    ColumnAtLine,
    SurfaceAtLine,
    ObjectAtLine,
    DiscourseAtLine,
    DivisionAtLine,
    CompositeAtLine,
)
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.dollar_line import (
    LooseDollarLine,
    ImageDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
    SealDollarLine,
)
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.labels import ColumnLabel, ObjectLabel, SurfaceLabel
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.note_line import (
    EmphasisPart,
    LanguagePart,
    NoteLine,
    StringPart,
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
    Tabulation,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import InWordNewline, Word


class FragmentFactory(factory.Factory):  # pyre-ignore[11]
    class Meta:
        model = Fragment

    number = factory.Sequence(lambda n: MuseumNumber("X", str(n)))
    cdli_number = factory.Sequence(lambda n: f"cdli-{n}")
    bm_id_number = factory.Sequence(lambda n: f"bmId-{n}")
    accession = factory.Sequence(lambda n: f"accession-{n}")
    museum = factory.Faker("word")
    collection = factory.Faker("word")
    publication = factory.Faker("sentence")
    description = factory.Faker("text")
    script = factory.Iterator(["NA", "NB"])
    folios = Folios((Folio("WGL", "1"), Folio("XXX", "1")))
    genres = factory.Iterator(
        [
            (
                Genre(["ARCHIVAL", "Administrative", "Lists", "One Entry"], False),
                Genre(["CANONICAL", "Catalogues"], False),
            ),
            (Genre(["ARCHIVAL", "Administrative", "Lists", "One Entry"], False),),
        ]
    )


class InterestingFragmentFactory(FragmentFactory):
    collection = "Kuyunjik"
    publication = ""
    joins: Sequence[str] = tuple()
    text = Text()
    uncurated_references = (
        UncuratedReference("7(0)"),
        UncuratedReference("CAD 51", (34, 56)),
        UncuratedReference("7(1)"),
    )


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
        )
    )
    signs = (
        "X BA KU ABZ075 ABZ207a\\u002F207b\\u0020X ABZ377n1/KU ABZ377n1 ABZ411\n"
        "MI DIŠ UD ŠU\n"
        "KI DU ABZ411 BA MA TI\n"
        "X MU TA MA UD\n"
        "ŠU/|BI×IS|"
    )
    folios = Folios((Folio("WGL", "3"), Folio("XXX", "3")))
    record = factory.SubFactory(RecordFactory)
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
        )
    )
