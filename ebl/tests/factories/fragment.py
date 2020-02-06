from typing import Tuple

import factory

from ebl.dictionary.domain.word import WordId
from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.fragmentarium.domain.fragment import Fragment, UncuratedReference
from ebl.tests.factories.record import RecordFactory
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.line import TextLine
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
    joins: Tuple[str, ...] = tuple()
    text = Text()
    uncurated_references = (
        UncuratedReference("7(0)"),
        UncuratedReference("CAD 51", (34, 56)),
        UncuratedReference("7(1)"),
    )


class TransliteratedFragmentFactory(FragmentFactory):
    text = Text(
        (
            TextLine(
                "1'.",
                (
                    Word("X", parts=[UnidentifiedSign()]),
                    Word(
                        "BA<(ku-u₄)>",
                        parts=[
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
                    Column(),
                    Tabulation("($___$)"),
                    Word(
                        "[...-ku]-nu-ši",
                        parts=[
                            BrokenAway.open(),
                            UnknownNumberOfSigns(),
                            Joiner.hyphen(),
                            Reading.of_name("ku"),
                            BrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name("nu"),
                            Joiner.hyphen(),
                            Reading.of_name("ši"),
                        ],
                    ),
                    Variant.of(
                        Divider.of(":"), Word("ku", parts=[Reading.of_name("ku")])
                    ),
                    BrokenAway.open(),
                    UnknownNumberOfSigns(),
                    BrokenAway.close(),
                    Column(2),
                    Divider.of(":", ("@v",), (Flag.DAMAGE,)),
                    CommentaryProtocol("!qt"),
                    Word("10#", parts=[Number.of_name("10", flags=[Flag.DAMAGE])]),
                ),
            ),
            TextLine(
                "2'.",
                (
                    BrokenAway.open(),
                    UnknownNumberOfSigns(),
                    BrokenAway.close(),
                    Word("GI₆", parts=[Logogram.of_name("GI", 6)]),
                    Word("ana", parts=[Reading.of_name("ana")]),
                    Word(
                        "u₄-š[u",
                        parts=[
                            Reading.of_name("u", 4),
                            Joiner.hyphen(),
                            Reading.of(
                                (ValueToken("š"), BrokenAway.open(), ValueToken("u"))
                            ),
                        ],
                    ),
                    UnknownNumberOfSigns(),
                    BrokenAway.close(),
                ),
            ),
            TextLine(
                "3'.",
                (
                    BrokenAway.open(),
                    UnknownNumberOfSigns(),
                    Word(
                        "k]i-du",
                        parts=[
                            Reading.of(
                                (ValueToken("k"), BrokenAway.close(), ValueToken("i"))
                            ),
                            Joiner.hyphen(),
                            Reading.of_name("du"),
                        ],
                    ),
                    Word("u", parts=[Reading.of_name("u")]),
                    Word(
                        "ba-ma-t[i",
                        parts=[
                            Reading.of_name("ba"),
                            Joiner.hyphen(),
                            Reading.of_name("ma"),
                            Joiner.hyphen(),
                            Reading.of(
                                (ValueToken("t"), BrokenAway.open(), ValueToken("i"))
                            ),
                        ],
                    ),
                    UnknownNumberOfSigns(),
                    BrokenAway.close(),
                ),
            ),
            TextLine(
                "6'.",
                (
                    BrokenAway.open(),
                    UnknownNumberOfSigns(),
                    BrokenAway.close(),
                    Word("x#", parts=[UnclearSign([Flag.DAMAGE])]),
                    Word("mu", parts=[Reading.of_name("mu")]),
                    Word(
                        "ta-ma;-tu₂",
                        parts=[
                            Reading.of_name("ta"),
                            Joiner.hyphen(),
                            Reading.of_name("ma"),
                            InWordNewline(),
                            Joiner.hyphen(),
                            Reading.of_name("tu₂"),
                        ],
                    ),
                ),
            ),
            TextLine(
                "7'.",
                (
                    Word(
                        "šu/|BI×IS|",
                        parts=[
                            Variant(
                                (Reading.of_name("šu"), CompoundGrapheme("|BI×IS|"))
                            )
                        ],
                    ),
                ),
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
            TextLine(
                "1'.",
                (
                    Word("X", parts=[UnidentifiedSign()]),
                    Word(
                        "BA<(ku-u₄)>",
                        parts=[
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
                    Column(),
                    Tabulation("($___$)"),
                    Word(
                        "[...-ku]-nu-ši",
                        parts=[
                            BrokenAway.open(),
                            UnknownNumberOfSigns(),
                            Joiner.hyphen(),
                            Reading.of_name("ku"),
                            BrokenAway.close(),
                            Joiner.hyphen(),
                            Reading.of_name("nu"),
                            Joiner.hyphen(),
                            Reading.of_name("ši"),
                        ],
                    ),
                    Variant.of(
                        Divider.of(":"), Word("ku", parts=[Reading.of_name("ku")])
                    ),
                    BrokenAway.open(),
                    UnknownNumberOfSigns(),
                    BrokenAway.close(),
                    Column(2),
                    Divider.of(":", ("@v",), (Flag.DAMAGE,)),
                    CommentaryProtocol("!qt"),
                    Word("10#", parts=[Number.of_name("10", flags=[Flag.DAMAGE])]),
                ),
            ),
            TextLine(
                "2'.",
                (
                    BrokenAway.open(),
                    UnknownNumberOfSigns(),
                    Word(
                        "GI₆",
                        unique_lemma=(WordId("ginâ I"),),
                        parts=[Logogram.of_name("GI", 6)],
                    ),
                    Word(
                        "ana",
                        unique_lemma=(WordId("ana I"),),
                        parts=[Reading.of_name("ana")],
                    ),
                    Word(
                        "u₄-š[u",
                        unique_lemma=(WordId("ūsu I"),),
                        parts=[
                            Reading.of_name("u₄"),
                            Joiner.hyphen(),
                            Reading.of_name("š[u"),
                        ],
                    ),
                    UnknownNumberOfSigns(),
                    BrokenAway.close(),
                ),
            ),
            TextLine(
                "3'.",
                (
                    BrokenAway.open(),
                    UnknownNumberOfSigns(),
                    Word(
                        "k]i-du",
                        unique_lemma=(WordId("kīdu I"),),
                        parts=[
                            Reading.of(
                                (ValueToken("k"), BrokenAway.close(), ValueToken("i"))
                            ),
                            Joiner.hyphen(),
                            Reading.of_name("du"),
                        ],
                    ),
                    Word(
                        "u",
                        unique_lemma=(WordId("u I"),),
                        parts=[Reading.of_name("u")],
                    ),
                    Word(
                        "ba-ma-t[i",
                        unique_lemma=(WordId("bamātu I"),),
                        parts=[
                            Reading.of_name("ba"),
                            Joiner.hyphen(),
                            Reading.of_name("ma"),
                            Joiner.hyphen(),
                            Reading.of(
                                (ValueToken("t"), BrokenAway.open(), ValueToken("i"))
                            ),
                        ],
                    ),
                    UnknownNumberOfSigns(),
                    BrokenAway.close(),
                ),
            ),
            TextLine(
                "6'.",
                (
                    BrokenAway.open(),
                    UnknownNumberOfSigns(),
                    BrokenAway.close(),
                    Word("x#", parts=[UnclearSign([Flag.DAMAGE])]),
                    Word(
                        "mu",
                        unique_lemma=(WordId("mu I"),),
                        parts=[Reading.of_name("mu")],
                    ),
                    Word(
                        "ta-ma;-tu₂",
                        unique_lemma=(WordId("tamalāku I"),),
                        parts=[
                            Reading.of_name("ta"),
                            Joiner.hyphen(),
                            Reading.of_name("ma"),
                            InWordNewline(),
                            Joiner.hyphen(),
                            Reading.of_name("tu", 2),
                        ],
                    ),
                ),
            ),
            TextLine(
                "7'.",
                (
                    Word(
                        "šu/|BI×IS|",
                        parts=[
                            Variant(
                                (Reading.of_name("šu"), CompoundGrapheme("|BI×IS|"))
                            )
                        ],
                    ),
                ),
            ),
        )
    )
