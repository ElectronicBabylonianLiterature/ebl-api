"""Parsed-word test cases, part 1 of 5."""

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Determinative,
    LinguisticGloss,
)
from ebl.transliteration.domain.sign import SignName
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Grapheme,
    Logogram,
    Number,
    Reading,
)
from ebl.transliteration.domain.tokens import (
    Joiner,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.unknown_sign_tokens import (
    UnclearSign,
    UnidentifiedSign,
)
from ebl.transliteration.domain.word_tokens import Word

WORD_CASES = [
    ("...", Word.of([UnknownNumberOfSigns.of()])),
    ("x", Word.of([UnclearSign.of()])),
    ("X", Word.of([UnidentifiedSign.of()])),
    ("x?", Word.of([UnclearSign.of([atf.Flag.UNCERTAIN])])),
    ("X#", Word.of([UnidentifiedSign.of([atf.Flag.DAMAGE])])),
    ("12", Word.of([Number.of_name("12")])),
    (
        "1]2",
        Word.of(
            [Number.of((ValueToken.of("1"), BrokenAway.close(), ValueToken.of("2")))]
        ),
    ),
    (
        "1[2",
        Word.of(
            [Number.of((ValueToken.of("1"), BrokenAway.open(), ValueToken.of("2")))]
        ),
    ),
    ("ʾ", Word.of([Reading.of_name("ʾ")])),
    ("du₁₁", Word.of([Reading.of_name("du", 11)])),
    ("GAL", Word.of([Logogram.of_name("GAL")])),
    (
        "kur(GAL)",
        Word.of([Reading.of_name("kur", sign=Grapheme.of(SignName("GAL")))]),
    ),
    (
        "KUR(GAL)",
        Word.of([Logogram.of_name("KUR", sign=Grapheme.of(SignName("GAL")))]),
    ),
    (
        "kur(|GAL|)",
        Word.of([Reading.of_name("kur", sign=CompoundGrapheme.of(["GAL"]))]),
    ),
    (
        "KUR(|GAL|)",
        Word.of([Logogram.of_name("KUR", sign=CompoundGrapheme.of(["GAL"]))]),
    ),
    ("|GAL|", Word.of([CompoundGrapheme.of(["GAL"])])),
    ("|U₄&KAM₂|", Word.of([CompoundGrapheme.of(["U₄&KAM₂"])])),
    ("|BI.IS|", Word.of([CompoundGrapheme.of(["BI", "IS"])])),
    ("|BI×(IS.IS)|", Word.of([CompoundGrapheme.of(["BI×(IS.IS)"])])),
    ("x-ti", Word.of([UnclearSign.of(), Joiner.hyphen(), Reading.of_name("ti")])),
    ("x.ti", Word.of([UnclearSign.of(), Joiner.dot(), Reading.of_name("ti")])),
    ("x+ti", Word.of([UnclearSign.of(), Joiner.plus(), Reading.of_name("ti")])),
    ("x:ti", Word.of([UnclearSign.of(), Joiner.colon(), Reading.of_name("ti")])),
    (
        "ti-X",
        Word.of([Reading.of_name("ti"), Joiner.hyphen(), UnidentifiedSign.of()]),
    ),
    (
        "r]u-u₂-qu",
        Word.of(
            [
                Reading.of(
                    (ValueToken.of("r"), BrokenAway.close(), ValueToken.of("u"))
                ),
                Joiner.hyphen(),
                Reading.of_name("u", 2),
                Joiner.hyphen(),
                Reading.of_name("qu"),
            ]
        ),
    ),
    (
        "ru?-u₂-qu",
        Word.of(
            [
                Reading.of_name("ru", flags=[atf.Flag.UNCERTAIN]),
                Joiner.hyphen(),
                Reading.of_name("u", 2),
                Joiner.hyphen(),
                Reading.of_name("qu"),
            ]
        ),
    ),
    ("gid₂", Word.of([Reading.of_name("gid", 2)])),
    (
        "U₄].14.KAM₂",
        Word.of(
            [
                Logogram.of_name("U", 4),
                BrokenAway.close(),
                Joiner.dot(),
                Number.of_name("14"),
                Joiner.dot(),
                Logogram.of_name("KAM", 2),
            ]
        ),
    ),
    (
        "{ku}nu",
        Word.of([Determinative.of([Reading.of_name("ku")]), Reading.of_name("nu")]),
    ),
    (
        "{{ku}}nu",
        Word.of([LinguisticGloss.of([Reading.of_name("ku")]), Reading.of_name("nu")]),
    ),
    (
        "ku{{nu}}",
        Word.of([Reading.of_name("ku"), LinguisticGloss.of([Reading.of_name("nu")])]),
    ),
    (
        "ku{nu}",
        Word.of([Reading.of_name("ku"), Determinative.of([Reading.of_name("nu")])]),
    ),
    (
        "ku{{nu}}si",
        Word.of(
            [
                Reading.of_name("ku"),
                LinguisticGloss.of([Reading.of_name("nu")]),
                Reading.of_name("si"),
            ]
        ),
    ),
    (
        "{iti}]ŠE",
        Word.of(
            [
                Determinative.of([Reading.of_name("iti")]),
                BrokenAway.close(),
                Logogram.of_name("ŠE"),
            ]
        ),
    ),
    (
        "šu/|BI×IS|/BI",
        Word.of(
            [
                Variant.of(
                    Reading.of_name("šu"),
                    CompoundGrapheme.of(["BI×IS"]),
                    Logogram.of_name("BI"),
                )
            ]
        ),
    ),
    (
        "{kur}aš+šur",
        Word.of(
            [
                Determinative.of([Reading.of_name("kur")]),
                Reading.of_name("aš"),
                Joiner.plus(),
                Reading.of_name("šur"),
            ]
        ),
    ),
]
