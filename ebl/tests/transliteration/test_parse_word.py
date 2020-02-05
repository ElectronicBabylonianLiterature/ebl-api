import pytest
from lark import ParseError
from lark.exceptions import UnexpectedInput

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    IntentionalOmission,
    Determinative,
    Erasure,
    LinguisticGloss,
    AccidentalOmission,
    PhoneticGloss,
    Removal,
    BrokenAway,
    PerhapsBrokenAway,
)
from ebl.transliteration.domain.lark_parser import parse_word
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Grapheme,
    Logogram,
    Number,
    Reading,
    UnclearSign,
    UnidentifiedSign,
)
from ebl.transliteration.domain.tokens import (
    Joiner,
    UnknownNumberOfSigns,
    Variant,
)
from ebl.transliteration.domain.word_tokens import (
    InWordNewline,
    LoneDeterminative,
    Word,
)


@pytest.mark.parametrize("parser", [parse_word])
@pytest.mark.parametrize(
    "atf,expected",
    [
        ("x", Word("x", parts=[UnclearSign()])),
        ("X", Word("X", parts=[UnidentifiedSign()])),
        ("x?", Word("x?", parts=[UnclearSign([atf.Flag.UNCERTAIN])])),
        ("X#", Word("X#", parts=[UnidentifiedSign([atf.Flag.DAMAGE])])),
        ("12", Word("12", parts=[Number.of("12")])),
        ("1]2", Word("1]2", parts=[Number.of("1]2")])),
        ("1[2", Word("1[2", parts=[Number.of("1[2")])),
        ("ʾ", Word("ʾ", parts=[Reading.of("ʾ")])),
        ("du₁₁", Word("du₁₁", parts=[Reading.of("du", 11)])),
        ("GAL", Word("GAL", parts=[Logogram.of("GAL")])),
        (
            "kur(GAL)",
            Word("kur(GAL)", parts=[Reading.of("kur", sign=Grapheme.of("GAL"))]),
        ),
        (
            "KUR(GAL)",
            Word("KUR(GAL)", parts=[Logogram.of("KUR", sign=Grapheme.of("GAL"))]),
        ),
        (
            "kur(|GAL|)",
            Word(
                "kur(|GAL|)", parts=[Reading.of("kur", sign=CompoundGrapheme("|GAL|"))]
            ),
        ),
        (
            "KUR(|GAL|)",
            Word(
                "KUR(|GAL|)", parts=[Logogram.of("KUR", sign=CompoundGrapheme("|GAL|"))]
            ),
        ),
        ("|GAL|", Word("|GAL|", parts=[CompoundGrapheme("|GAL|")])),
        (
            "x-ti",
            Word("x-ti", parts=[UnclearSign(), Joiner.hyphen(), Reading.of("ti"),],),
        ),
        (
            "x.ti",
            Word("x.ti", parts=[UnclearSign(), Joiner.dot(), Reading.of("ti"),],),
        ),
        (
            "x+ti",
            Word("x+ti", parts=[UnclearSign(), Joiner.plus(), Reading.of("ti"),],),
        ),
        (
            "x:ti",
            Word("x:ti", parts=[UnclearSign(), Joiner.colon(), Reading.of("ti"),],),
        ),
        (
            "ti-X",
            Word(
                "ti-X", parts=[Reading.of("ti"), Joiner.hyphen(), UnidentifiedSign(),],
            ),
        ),
        (
            "r]u-u₂-qu",
            Word(
                "r]u-u₂-qu",
                parts=[
                    Reading.of("r]u"),
                    Joiner.hyphen(),
                    Reading.of("u", 2),
                    Joiner.hyphen(),
                    Reading.of("qu"),
                ],
            ),
        ),
        (
            "ru?-u₂-qu",
            Word(
                "ru?-u₂-qu",
                parts=[
                    Reading.of("ru", flags=[atf.Flag.UNCERTAIN]),
                    Joiner.hyphen(),
                    Reading.of("u", 2),
                    Joiner.hyphen(),
                    Reading.of("qu"),
                ],
            ),
        ),
        (
            "na-a[n-",
            Word(
                "na-a[n-",
                parts=[
                    Reading.of("na"),
                    Joiner.hyphen(),
                    Reading.of("a[n"),
                    Joiner.hyphen(),
                ],
            ),
        ),
        (
            "-ku]-nu",
            Word(
                "-ku]-nu",
                parts=[
                    Joiner.hyphen(),
                    Reading.of("ku"),
                    BrokenAway.close(),
                    Joiner.hyphen(),
                    Reading.of("nu"),
                ],
            ),
        ),
        ("gid₂", Word("gid₂", parts=[Reading.of("gid", 2)])),
        ("|U₄&KAM₂|", Word("|U₄&KAM₂|", parts=[CompoundGrapheme("|U₄&KAM₂|")])),
        (
            "U₄].14.KAM₂",
            Word(
                "U₄].14.KAM₂",
                parts=[
                    Logogram.of("U", 4),
                    BrokenAway.close(),
                    Joiner.dot(),
                    Number.of("14"),
                    Joiner.dot(),
                    Logogram.of("KAM", 2),
                ],
            ),
        ),
        (
            "{ku}nu",
            Word(
                "{ku}nu", parts=[Determinative([Reading.of("ku")]), Reading.of("nu"),],
            ),
        ),
        (
            "{{ku}}nu",
            Word(
                "{{ku}}nu",
                parts=[LinguisticGloss([Reading.of("ku"),]), Reading.of("nu"),],
            ),
        ),
        (
            "ku{{nu}}",
            Word(
                "ku{{nu}}",
                parts=[Reading.of("ku"), LinguisticGloss([Reading.of("nu"),]),],
            ),
        ),
        (
            "ku{nu}",
            Word(
                "ku{nu}", parts=[Reading.of("ku"), Determinative([Reading.of("nu")]),],
            ),
        ),
        (
            "ku{{nu}}si",
            Word(
                "ku{{nu}}si",
                parts=[
                    Reading.of("ku"),
                    LinguisticGloss([Reading.of("nu"),]),
                    Reading.of("si"),
                ],
            ),
        ),
        (
            "{iti}]ŠE",
            Word(
                "{iti}]ŠE",
                parts=[
                    Determinative([Reading.of("iti")]),
                    BrokenAway.close(),
                    Logogram.of("ŠE"),
                ],
            ),
        ),
        (
            "šu/|BI×IS|/BI",
            Word(
                "šu/|BI×IS|/BI",
                parts=[
                    Variant(
                        (
                            Reading.of("šu"),
                            CompoundGrapheme("|BI×IS|"),
                            Logogram.of("BI"),
                        )
                    )
                ],
            ),
        ),
        (
            "{kur}aš+šur",
            Word(
                "{kur}aš+šur",
                parts=[
                    Determinative([Reading.of("kur")]),
                    Reading.of("aš"),
                    Joiner.plus(),
                    Reading.of("šur"),
                ],
            ),
        ),
        (
            "i-le-ʾe-[e",
            Word(
                "i-le-ʾe-[e",
                parts=[
                    Reading.of("i"),
                    Joiner.hyphen(),
                    Reading.of("le"),
                    Joiner.hyphen(),
                    Reading.of("ʾe"),
                    Joiner.hyphen(),
                    BrokenAway.open(),
                    Reading.of("e"),
                ],
            ),
        ),
        (
            "U₄.27/29.KAM",
            Word(
                "U₄.27/29.KAM",
                parts=[
                    Logogram.of("U", 4),
                    Joiner.dot(),
                    Variant((Number.of("27"), Number.of("29"))),
                    Joiner.dot(),
                    Logogram.of("KAM"),
                ],
            ),
        ),
        ("x/m[a", Word("x/m[a", parts=[Variant((UnclearSign(), Reading.of("m[a")))])),
        (
            "SAL.{+mu-ru-ub}",
            Word(
                "SAL.{+mu-ru-ub}",
                parts=[
                    Logogram.of("SAL"),
                    Joiner.dot(),
                    PhoneticGloss(
                        [
                            Reading.of("mu"),
                            Joiner.hyphen(),
                            Reading.of("ru"),
                            Joiner.hyphen(),
                            Reading.of("ub"),
                        ]
                    ),
                ],
            ),
        ),
        (
            "{+mu-ru-ub}[LA",
            Word(
                "{+mu-ru-ub}[LA",
                parts=[
                    PhoneticGloss(
                        [
                            Reading.of("mu"),
                            Joiner.hyphen(),
                            Reading.of("ru"),
                            Joiner.hyphen(),
                            Reading.of("ub"),
                        ]
                    ),
                    BrokenAway.open(),
                    Logogram.of("LA"),
                ],
            ),
        ),
        (
            "I.{d}",
            Word(
                "I.{d}",
                parts=[
                    Logogram.of("I"),
                    Joiner.dot(),
                    Determinative([Reading.of("d")]),
                ],
            ),
        ),
        (
            "{d}[UTU?",
            Word(
                "{d}[UTU?",
                parts=[
                    Determinative([Reading.of("d")]),
                    BrokenAway.open(),
                    Logogram.of("UTU", flags=[atf.Flag.UNCERTAIN]),
                ],
            ),
        ),
        (
            ".x.KAM",
            Word(
                ".x.KAM",
                parts=[Joiner.dot(), UnclearSign(), Joiner.dot(), Logogram.of("KAM"),],
            ),
        ),
        (
            "3.AM₃",
            Word("3.AM₃", parts=[Number.of("3"), Joiner.dot(), Logogram.of("AM", 3),],),
        ),
        (
            "<{10}>bu",
            Word(
                "<{10}>bu",
                parts=[
                    AccidentalOmission.open(),
                    Determinative([Number.of("10")]),
                    AccidentalOmission.close(),
                    Reading.of("bu"),
                ],
            ),
        ),
        (
            "KA₂?].DINGIR.RA[{ki?}",
            Word(
                "KA₂?].DINGIR.RA[{ki?}",
                parts=[
                    Logogram.of("KA", 2, flags=[atf.Flag.UNCERTAIN]),
                    BrokenAway.close(),
                    Joiner.dot(),
                    Logogram.of("DINGIR"),
                    Joiner.dot(),
                    Logogram.of("RA"),
                    BrokenAway.open(),
                    Determinative([Reading.of("ki", flags=[atf.Flag.UNCERTAIN])]),
                ],
            ),
        ),
        (
            "{d?}nu?-di]m₂?-mu[d?",
            Word(
                "{d?}nu?-di]m₂?-mu[d?",
                parts=[
                    Determinative([Reading.of("d", flags=[atf.Flag.UNCERTAIN])]),
                    Reading.of("nu", flags=[atf.Flag.UNCERTAIN]),
                    Joiner.hyphen(),
                    Reading.of("di]m", 2, flags=[atf.Flag.UNCERTAIN]),
                    Joiner.hyphen(),
                    Reading.of("mu[d", flags=[atf.Flag.UNCERTAIN]),
                ],
            ),
        ),
        (
            "<GAR?>",
            Word(
                "<GAR?>",
                parts=[
                    AccidentalOmission.open(),
                    Logogram.of("GAR", flags=[atf.Flag.UNCERTAIN]),
                    AccidentalOmission.close(),
                ],
            ),
        ),
        (
            "<<GAR>>",
            Word(
                "<<GAR>>", parts=[Removal.open(), Logogram.of("GAR"), Removal.close(),],
            ),
        ),
        ("lu₂@v", Word("lu₂@v", parts=[Reading.of("lu", 2, modifiers=["@v"])]),),
        (
            "{lu₂@v}UM.ME.[A",
            Word(
                "{lu₂@v}UM.ME.[A",
                parts=[
                    Determinative([Reading.of("lu", 2, modifiers=["@v"])]),
                    Logogram.of("UM"),
                    Joiner.dot(),
                    Logogram.of("ME"),
                    Joiner.dot(),
                    BrokenAway.open(),
                    Logogram.of("A"),
                ],
            ),
        ),
        (
            "{lu₂@v}]KAB.SAR-M[EŠ",
            Word(
                "{lu₂@v}]KAB.SAR-M[EŠ",
                parts=[
                    Determinative([Reading.of("lu", 2, modifiers=["@v"])]),
                    BrokenAway.close(),
                    Logogram.of("KAB"),
                    Joiner.dot(),
                    Logogram.of("SAR"),
                    Joiner.hyphen(),
                    Logogram.of("M[EŠ"),
                ],
            ),
        ),
        (
            "MIN<(ta-ne₂-hi)>",
            Word(
                "MIN<(ta-ne₂-hi)>",
                parts=[
                    Logogram.of(
                        "MIN",
                        surrogate=[
                            Reading.of("ta"),
                            Joiner.hyphen(),
                            Reading.of("ne", 2),
                            Joiner.hyphen(),
                            Reading.of("hi"),
                        ],
                    )
                ],
            ),
        ),
        (
            "MIN<(mu-u₂)>",
            Word(
                "MIN<(mu-u₂)>",
                parts=[
                    Logogram.of(
                        "MIN",
                        surrogate=[
                            Reading.of("mu"),
                            Joiner.hyphen(),
                            Reading.of("u", 2),
                        ],
                    )
                ],
            ),
        ),
        (
            "KIMIN<(mu-u₂)>",
            Word(
                "KIMIN<(mu-u₂)>",
                parts=[
                    Logogram.of(
                        "KIMIN",
                        surrogate=[
                            Reading.of("mu"),
                            Joiner.hyphen(),
                            Reading.of("u", 2),
                        ],
                    )
                ],
            ),
        ),
        ("UN#", Word("UN#", parts=[Logogram.of("UN", flags=[atf.Flag.DAMAGE])])),
        (
            "he₂-<(pa₃)>",
            Word(
                "he₂-<(pa₃)>",
                parts=[
                    Reading.of("he", 2),
                    Joiner.hyphen(),
                    IntentionalOmission.open(),
                    Reading.of("pa", 3),
                    IntentionalOmission.close(),
                ],
            ),
        ),
        (
            "{[i]ti}AB",
            Word(
                "{[i]ti}AB",
                parts=[
                    Determinative([BrokenAway.open(), Reading.of("i]ti")]),
                    Logogram.of("AB"),
                ],
            ),
        ),
        (
            "in]-",
            Word(
                "in]-", parts=[Reading.of("in"), BrokenAway.close(), Joiner.hyphen(),],
            ),
        ),
        (
            "<en-da-ab>",
            Word(
                "<en-da-ab>",
                parts=[
                    AccidentalOmission.open(),
                    Reading.of("en"),
                    Joiner.hyphen(),
                    Reading.of("da"),
                    Joiner.hyphen(),
                    Reading.of("ab"),
                    AccidentalOmission.close(),
                ],
            ),
        ),
        (
            "me-e-li-°\\ku°",
            Word(
                "me-e-li-°\\ku°",
                parts=[
                    Reading.of("me"),
                    Joiner.hyphen(),
                    Reading.of("e"),
                    Joiner.hyphen(),
                    Reading.of("li"),
                    Joiner.hyphen(),
                    Erasure.open(),
                    Erasure.center(),
                    Reading.of("ku"),
                    Erasure.close(),
                ],
            ),
        ),
        (
            "°me-e-li\\°-ku",
            Word(
                "°me-e-li\\°-ku",
                parts=[
                    Erasure.open(),
                    Reading.of("me"),
                    Joiner.hyphen(),
                    Reading.of("e"),
                    Joiner.hyphen(),
                    Reading.of("li"),
                    Erasure.center(),
                    Erasure.close(),
                    Joiner.hyphen(),
                    Reading.of("ku"),
                ],
            ),
        ),
        (
            "me-°e\\li°-ku",
            Word(
                "me-°e\\li°-ku",
                parts=[
                    Reading.of("me"),
                    Joiner(atf.Joiner.HYPHEN),
                    Erasure.open(),
                    Reading.of("e"),
                    Erasure.center(),
                    Reading.of("li"),
                    Erasure.close(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("ku"),
                ],
            ),
        ),
        (
            "me-°e\\li°-me-°e\\li°-ku",
            Word(
                "me-°e\\li°-me-°e\\li°-ku",
                parts=[
                    Reading.of("me"),
                    Joiner(atf.Joiner.HYPHEN),
                    Erasure.open(),
                    Reading.of("e"),
                    Erasure.center(),
                    Reading.of("li"),
                    Erasure.close(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("me"),
                    Joiner(atf.Joiner.HYPHEN),
                    Erasure.open(),
                    Reading.of("e"),
                    Erasure.center(),
                    Reading.of("li"),
                    Erasure.close(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("ku"),
                ],
            ),
        ),
        (
            "...{d}kur",
            Word(
                "...{d}kur",
                parts=[
                    UnknownNumberOfSigns(),
                    Determinative([Reading.of("d")]),
                    Reading.of("kur"),
                ],
            ),
        ),
        (
            "kur{d}...",
            Word(
                "kur{d}...",
                parts=[
                    Reading.of("kur"),
                    Determinative([Reading.of("d")]),
                    UnknownNumberOfSigns(),
                ],
            ),
        ),
        (
            "...-kur-...",
            Word(
                "...-kur-...",
                parts=[
                    UnknownNumberOfSigns(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("kur"),
                    Joiner(atf.Joiner.HYPHEN),
                    UnknownNumberOfSigns(),
                ],
            ),
        ),
        (
            "kur-...-kur-...-kur",
            Word(
                "kur-...-kur-...-kur",
                parts=[
                    Reading.of("kur"),
                    Joiner(atf.Joiner.HYPHEN),
                    UnknownNumberOfSigns(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("kur"),
                    Joiner(atf.Joiner.HYPHEN),
                    UnknownNumberOfSigns(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("kur"),
                ],
            ),
        ),
        (
            "...]-ku",
            Word(
                "...]-ku",
                parts=[
                    UnknownNumberOfSigns(),
                    BrokenAway.close(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("ku"),
                ],
            ),
        ),
        (
            "ku-[...",
            Word(
                "ku-[...",
                parts=[
                    Reading.of("ku"),
                    Joiner(atf.Joiner.HYPHEN),
                    BrokenAway.open(),
                    UnknownNumberOfSigns(),
                ],
            ),
        ),
        (
            "....ku",
            Word(
                "....ku",
                parts=[UnknownNumberOfSigns(), Joiner.dot(), Reading.of("ku"),],
            ),
        ),
        (
            "ku....",
            Word(
                "ku....",
                parts=[Reading.of("ku"), Joiner.dot(), UnknownNumberOfSigns(),],
            ),
        ),
        (
            "(x)]",
            Word(
                "(x)]",
                parts=[
                    PerhapsBrokenAway.open(),
                    UnclearSign(),
                    PerhapsBrokenAway.close(),
                    BrokenAway.close(),
                ],
            ),
        ),
        (
            "[{d}UTU",
            Word(
                "[{d}UTU",
                parts=[
                    BrokenAway.open(),
                    Determinative([Reading.of("d")]),
                    Logogram.of("UTU"),
                ],
            ),
        ),
        (
            "{m#}[{d}AG-sa-lim",
            Word(
                "{m#}[{d}AG-sa-lim",
                parts=[
                    Determinative([Reading.of("m", flags=[atf.Flag.DAMAGE])]),
                    BrokenAway.open(),
                    Determinative([Reading.of("d")]),
                    Logogram.of("AG"),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("sa"),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("lim"),
                ],
            ),
        ),
        (
            "ša#-[<(mu-un-u₅)>]",
            Word(
                "ša#-[<(mu-un-u₅)>]",
                parts=[
                    Reading.of("ša", flags=[atf.Flag.DAMAGE]),
                    Joiner(atf.Joiner.HYPHEN),
                    BrokenAway.open(),
                    IntentionalOmission.open(),
                    Reading.of("mu"),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("un"),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("u", 5),
                    IntentionalOmission.close(),
                    BrokenAway.close(),
                ],
            ),
        ),
        (
            "|UM×(ME.DA)|-b[i?",
            Word(
                "|UM×(ME.DA)|-b[i?",
                parts=[
                    CompoundGrapheme("|UM×(ME.DA)|"),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("b[i", flags=[atf.Flag.UNCERTAIN]),
                ],
            ),
        ),
        (
            "mu-un;-e₃",
            Word(
                "mu-un;-e₃",
                parts=[
                    Reading.of("mu"),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("un"),
                    InWordNewline(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("e", 3),
                ],
            ),
        ),
        (
            "du₃-am₃{{mu-un-<(du₃)>}}",
            Word(
                "du₃-am₃{{mu-un-<(du₃)>}}",
                parts=[
                    Reading.of("du", 3),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of("am", 3),
                    LinguisticGloss(
                        [
                            Reading.of("mu"),
                            Joiner(atf.Joiner.HYPHEN),
                            Reading.of("un"),
                            Joiner(atf.Joiner.HYPHEN),
                            IntentionalOmission.open(),
                            Reading.of("du", 3),
                            IntentionalOmission.close(),
                        ]
                    ),
                ],
            ),
        ),
        ("kurₓ", Word("kurₓ", parts=[Reading.of("kur", None),]),),
        ("KURₓ", Word("KURₓ", parts=[Logogram.of("KUR", None),]),),
        (
            "kurₓ(KUR)",
            Word(
                "kurₓ(KUR)", parts=[Reading.of("kur", None, sign=Grapheme.of("KUR")),]
            ),
        ),
    ],
)
def test_word(parser, atf, expected):
    assert parser(atf) == expected


@pytest.mark.parametrize("parser", [parse_word])
@pytest.mark.parametrize(
    "atf,expected",
    [
        (
            "<{10}>",
            LoneDeterminative(
                "<{10}>",
                parts=[
                    AccidentalOmission.open(),
                    Determinative([Number.of("10")]),
                    AccidentalOmission.close(),
                ],
            ),
        ),
        (
            "{ud]u?}",
            LoneDeterminative(
                "{ud]u?}",
                parts=[
                    Determinative([Reading.of("ud]u", flags=[atf.Flag.UNCERTAIN])]),
                ],
            ),
        ),
        (
            "{u₂#}",
            LoneDeterminative(
                "{u₂#}",
                parts=[Determinative([Reading.of("u", 2, flags=[atf.Flag.DAMAGE])]),],
            ),
        ),
        (
            "{lu₂@v}",
            LoneDeterminative(
                "{lu₂@v}",
                parts=[Determinative([Reading.of("lu", 2, modifiers=["@v"])]),],
            ),
        ),
        (
            "{k[i]}",
            LoneDeterminative(
                "{k[i]}",
                parts=[Determinative([Reading.of("k[i"), BrokenAway.close()]),],
            ),
        ),
        (
            "{[k]i}",
            LoneDeterminative(
                "{[k]i}",
                parts=[Determinative([BrokenAway.open(), Reading.of("k]i")]),],
            ),
        ),
    ],
)
def test_lone_determinative(parser, atf, expected):
    assert parser(atf) == expected


@pytest.mark.parametrize("parser", [parse_word])
@pytest.mark.parametrize("atf", ["{udu}?"])
def test_invalid_lone_determinative(parser, atf):
    with pytest.raises(UnexpectedInput):
        parser(atf)


@pytest.mark.parametrize("parser", [parse_word])
@pytest.mark.parametrize(
    "invalid_atf",
    [
        "Kur" "ku(r",
        "K)UR",
        "K[(UR",
        "ku)]r",
        "sal/: šim",
        "<GAR>?",
        "KA₂]?.DINGIR.RA[{ki?}",
        "KA₂?].DINGIR.RA[{ki}?",
        "k[a]?",
        ":-sal",
        "gam/:" "//sal",
        "Š[A₃?...]",
        "0",
        "01",
        "|KU]R|",
        "|KUR.[KUR|",
    ],
)
def test_invalid(parser, invalid_atf):
    with pytest.raises((UnexpectedInput, ParseError)):
        parser(invalid_atf)
