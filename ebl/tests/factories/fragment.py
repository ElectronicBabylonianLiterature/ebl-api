from typing import Sequence

import factory

from ebl.dictionary.domain.word import WordId
from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.fragmentarium.domain.fragment import Fragment, UncuratedReference
from ebl.tests.factories.record import RecordFactory
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.dollar_line import (
    ImageDollarLine,
    LooseDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
)
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.note_line import (
    EmphasisPart,
    LanguagePart,
    NoteLine,
    StringPart,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Divider,
    Logogram,
    Number,
    Reading,
    UnclearSign,
    UnidentifiedSign,
)
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.tokens import (
    Column,
    CommentaryProtocol,
    Joiner,
    Tabulation,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.word_tokens import InWordNewline, Word


class FragmentFactory(factory.Factory):
    class Meta:
        model = Fragment

    number = factory.Sequence(lambda n: f"X.{n}")
    cdli_number = factory.Sequence(lambda n: f"cdli-{n}")
    bm_id_number = factory.Sequence(lambda n: f"bmId-{n}")
    accession = factory.Sequence(lambda n: f"accession-{n}")
    museum = factory.Faker("word")
    collection = factory.Faker("word")
    publication = factory.Faker("sentence")
    description = factory.Faker("text")
    script = factory.Iterator(["NA", "NB"])
    folios = Folios((Folio("WGL", "1"), Folio("XXX", "1")))


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
            TextLine.of_legacy_iterable(
                LineNumberLabel.from_atf("1'."),
                (
                    Word.of([UnidentifiedSign(frozenset())]),
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
                    Tabulation(frozenset(), "($___$)"),
                    Word.of(
                        [
                            BrokenAway.open(),
                            UnknownNumberOfSigns(frozenset()),
                            Joiner.hyphen(),
                            Reading.of_name("ku"),
                            BrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name("nu"),
                            Joiner.hyphen(),
                            Reading.of_name("ši"),
                        ],
                    ),
                    Variant.of(Divider.of(":"), Reading.of_name("ku")),
                    BrokenAway.open(),
                    UnknownNumberOfSigns(frozenset()),
                    BrokenAway.close(),
                    Column.of(2),
                    Divider.of(":", ("@v",), (Flag.DAMAGE,)),
                    CommentaryProtocol(frozenset(), "!qt"),
                    Word.of([Number.of_name("10", flags=[Flag.DAMAGE])]),
                ),
            ),
            TextLine.of_legacy_iterable(
                LineNumberLabel.from_atf("2'."),
                (
                    BrokenAway.open(),
                    UnknownNumberOfSigns(frozenset()),
                    BrokenAway.close(),
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
                        ],
                    ),
                    UnknownNumberOfSigns(frozenset()),
                    BrokenAway.close(),
                ),
            ),
            TextLine.of_legacy_iterable(
                LineNumberLabel.from_atf("3'."),
                (
                    BrokenAway.open(),
                    UnknownNumberOfSigns(frozenset()),
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
                        ],
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
                        ],
                    ),
                    UnknownNumberOfSigns(frozenset()),
                    BrokenAway.close(),
                ),
            ),
            TextLine.of_legacy_iterable(
                LineNumberLabel.from_atf("6'."),
                (
                    BrokenAway.open(),
                    UnknownNumberOfSigns(frozenset()),
                    BrokenAway.close(),
                    Word.of([UnclearSign.of([Flag.DAMAGE])]),
                    Word.of([Reading.of_name("mu")]),
                    Word.of(
                        [
                            Reading.of_name("ta"),
                            Joiner.hyphen(),
                            Reading.of_name("ma"),
                            InWordNewline(frozenset()),
                            Joiner.hyphen(),
                            Reading.of_name("tu", 2),
                        ],
                    ),
                ),
            ),
            TextLine.of_legacy_iterable(
                LineNumberLabel.from_atf("7'."),
                (
                    Word.of(
                        [
                            Variant.of(
                                Reading.of_name("šu"), CompoundGrapheme.of("|BI×IS|")
                            )
                        ],
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
            NoteLine(
                (
                    StringPart("a note "),
                    EmphasisPart("italic"),
                    LanguagePart("Akkadian", Language.AKKADIAN),
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


class LemmatizedFragmentFactory(TransliteratedFragmentFactory):
    text = Text(
        (
            TextLine.of_legacy_iterable(
                LineNumberLabel.from_atf("1'."),
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
                        ],
                    ),
                    Column.of(),
                    Tabulation.of("($___$)"),
                    Word.of(
                        [
                            BrokenAway.open(),
                            UnknownNumberOfSigns(frozenset()),
                            Joiner.hyphen(),
                            Reading.of_name("ku"),
                            BrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name("nu"),
                            Joiner.hyphen(),
                            Reading.of_name("ši"),
                        ],
                    ),
                    Variant.of(Divider.of(":"), Reading.of_name("ku")),
                    BrokenAway.open(),
                    UnknownNumberOfSigns(frozenset()),
                    BrokenAway.close(),
                    Column.of(2),
                    Divider.of(":", ("@v",), (Flag.DAMAGE,)),
                    CommentaryProtocol.of("!qt"),
                    Word.of([Number.of_name("10", flags=[Flag.DAMAGE])]),
                ),
            ),
            TextLine.of_legacy_iterable(
                LineNumberLabel.from_atf("2'."),
                (
                    BrokenAway.open(),
                    UnknownNumberOfSigns(frozenset()),
                    Word.of(
                        [Logogram.of_name("GI", 6)], unique_lemma=(WordId("ginâ I"),),
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
                    UnknownNumberOfSigns(frozenset()),
                    BrokenAway.close(),
                ),
            ),
            TextLine.of_legacy_iterable(
                LineNumberLabel.from_atf("3'."),
                (
                    BrokenAway.open(),
                    UnknownNumberOfSigns(frozenset()),
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
                        unique_lemma=(WordId("u I"),), parts=[Reading.of_name("u")],
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
                    UnknownNumberOfSigns(frozenset()),
                    BrokenAway.close(),
                ),
            ),
            TextLine.of_legacy_iterable(
                LineNumberLabel.from_atf("6'."),
                (
                    BrokenAway.open(),
                    UnknownNumberOfSigns(frozenset()),
                    BrokenAway.close(),
                    Word.of([UnclearSign.of([Flag.DAMAGE])]),
                    Word.of(
                        unique_lemma=(WordId("mu I"),), parts=[Reading.of_name("mu")],
                    ),
                    Word.of(
                        unique_lemma=(WordId("tamalāku I"),),
                        parts=[
                            Reading.of_name("ta"),
                            Joiner.hyphen(),
                            Reading.of_name("ma"),
                            InWordNewline(frozenset()),
                            Joiner.hyphen(),
                            Reading.of_name("tu", 2),
                        ],
                    ),
                ),
            ),
            TextLine.of_legacy_iterable(
                LineNumberLabel.from_atf("7'."),
                (
                    Word.of(
                        [
                            Variant.of(
                                Reading.of_name("šu"), CompoundGrapheme.of("|BI×IS|")
                            )
                        ],
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
            NoteLine(
                (
                    StringPart("a note "),
                    EmphasisPart("italic"),
                    LanguagePart("Akkadian", Language.AKKADIAN),
                )
            ),
        )
    )
