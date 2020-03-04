import pytest
from lark import ParseError
from lark.exceptions import UnexpectedInput

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    Determinative,
    Erasure,
    IntentionalOmission,
    LinguisticGloss,
    PerhapsBrokenAway,
    PhoneticGloss,
    Removal,
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
    ValueToken,
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
        ("x", Word(parts=[UnclearSign()])),
        ("X", Word(parts=[UnidentifiedSign()])),
        ("x?", Word(parts=[UnclearSign([atf.Flag.UNCERTAIN])])),
        ("X#", Word(parts=[UnidentifiedSign([atf.Flag.DAMAGE])])),
        ("12", Word(parts=[Number.of_name("12")])),
        (
            "1]2",
            Word(
                parts=[
                    Number.of((ValueToken("1"), BrokenAway.close(), ValueToken("2")))
                ],
            ),
        ),
        (
            "1[2",
            Word(
                parts=[
                    Number.of((ValueToken("1"), BrokenAway.open(), ValueToken("2")))
                ],
            ),
        ),
        ("ʾ", Word(parts=[Reading.of_name("ʾ")])),
        ("du₁₁", Word(parts=[Reading.of_name("du", 11)])),
        ("GAL", Word(parts=[Logogram.of_name("GAL")])),
        ("kur(GAL)", Word(parts=[Reading.of_name("kur", sign=Grapheme.of("GAL"))]),),
        ("KUR(GAL)", Word(parts=[Logogram.of_name("KUR", sign=Grapheme.of("GAL"))]),),
        (
            "kur(|GAL|)",
            Word(parts=[Reading.of_name("kur", sign=CompoundGrapheme("|GAL|"))],),
        ),
        (
            "KUR(|GAL|)",
            Word(parts=[Logogram.of_name("KUR", sign=CompoundGrapheme("|GAL|"))],),
        ),
        ("|GAL|", Word(parts=[CompoundGrapheme("|GAL|")])),
        (
            "x-ti",
            Word(parts=[UnclearSign(), Joiner.hyphen(), Reading.of_name("ti"),],),
        ),
        ("x.ti", Word(parts=[UnclearSign(), Joiner.dot(), Reading.of_name("ti"),],),),
        ("x+ti", Word(parts=[UnclearSign(), Joiner.plus(), Reading.of_name("ti"),],),),
        ("x:ti", Word(parts=[UnclearSign(), Joiner.colon(), Reading.of_name("ti"),],),),
        (
            "ti-X",
            Word(parts=[Reading.of_name("ti"), Joiner.hyphen(), UnidentifiedSign(),],),
        ),
        (
            "r]u-u₂-qu",
            Word(
                parts=[
                    Reading.of((ValueToken("r"), BrokenAway.close(), ValueToken("u"))),
                    Joiner.hyphen(),
                    Reading.of_name("u", 2),
                    Joiner.hyphen(),
                    Reading.of_name("qu"),
                ],
            ),
        ),
        (
            "ru?-u₂-qu",
            Word(
                parts=[
                    Reading.of_name("ru", flags=[atf.Flag.UNCERTAIN]),
                    Joiner.hyphen(),
                    Reading.of_name("u", 2),
                    Joiner.hyphen(),
                    Reading.of_name("qu"),
                ],
            ),
        ),
        (
            "na-a[n-",
            Word(
                parts=[
                    Reading.of_name("na"),
                    Joiner.hyphen(),
                    Reading.of((ValueToken("a"), BrokenAway.open(), ValueToken("n"))),
                    Joiner.hyphen(),
                ],
            ),
        ),
        (
            "-ku]-nu",
            Word(
                parts=[
                    Joiner.hyphen(),
                    Reading.of_name("ku"),
                    BrokenAway.close(),
                    Joiner.hyphen(),
                    Reading.of_name("nu"),
                ],
            ),
        ),
        ("gid₂", Word(parts=[Reading.of_name("gid", 2)])),
        ("|U₄&KAM₂|", Word(parts=[CompoundGrapheme("|U₄&KAM₂|")])),
        (
            "U₄].14.KAM₂",
            Word(
                parts=[
                    Logogram.of_name("U", 4),
                    BrokenAway.close(),
                    Joiner.dot(),
                    Number.of_name("14"),
                    Joiner.dot(),
                    Logogram.of_name("KAM", 2),
                ],
            ),
        ),
        (
            "{ku}nu",
            Word(
                parts=[Determinative([Reading.of_name("ku")]), Reading.of_name("nu"),],
            ),
        ),
        (
            "{{ku}}nu",
            Word(
                parts=[
                    LinguisticGloss([Reading.of_name("ku"),]),
                    Reading.of_name("nu"),
                ],
            ),
        ),
        (
            "ku{{nu}}",
            Word(
                parts=[
                    Reading.of_name("ku"),
                    LinguisticGloss([Reading.of_name("nu"),]),
                ],
            ),
        ),
        (
            "ku{nu}",
            Word(
                parts=[Reading.of_name("ku"), Determinative([Reading.of_name("nu")]),],
            ),
        ),
        (
            "ku{{nu}}si",
            Word(
                parts=[
                    Reading.of_name("ku"),
                    LinguisticGloss([Reading.of_name("nu"),]),
                    Reading.of_name("si"),
                ],
            ),
        ),
        (
            "{iti}]ŠE",
            Word(
                parts=[
                    Determinative([Reading.of_name("iti")]),
                    BrokenAway.close(),
                    Logogram.of_name("ŠE"),
                ],
            ),
        ),
        (
            "šu/|BI×IS|/BI",
            Word(
                parts=[
                    Variant(
                        (
                            Reading.of_name("šu"),
                            CompoundGrapheme("|BI×IS|"),
                            Logogram.of_name("BI"),
                        )
                    )
                ],
            ),
        ),
        (
            "{kur}aš+šur",
            Word(
                parts=[
                    Determinative([Reading.of_name("kur")]),
                    Reading.of_name("aš"),
                    Joiner.plus(),
                    Reading.of_name("šur"),
                ],
            ),
        ),
        (
            "i-le-ʾe-[e",
            Word(
                parts=[
                    Reading.of_name("i"),
                    Joiner.hyphen(),
                    Reading.of_name("le"),
                    Joiner.hyphen(),
                    Reading.of_name("ʾe"),
                    Joiner.hyphen(),
                    BrokenAway.open(),
                    Reading.of_name("e"),
                ],
            ),
        ),
        (
            "U₄.27/29.KAM",
            Word(
                parts=[
                    Logogram.of_name("U", 4),
                    Joiner.dot(),
                    Variant((Number.of_name("27"), Number.of_name("29"))),
                    Joiner.dot(),
                    Logogram.of_name("KAM"),
                ],
            ),
        ),
        (
            "x/m[a",
            Word(
                parts=[
                    Variant(
                        (
                            UnclearSign(),
                            Reading.of(
                                (ValueToken("m"), BrokenAway.open(), ValueToken("a"))
                            ),
                        )
                    )
                ],
            ),
        ),
        (
            "SAL.{+mu-ru-ub}",
            Word(
                parts=[
                    Logogram.of_name("SAL"),
                    Joiner.dot(),
                    PhoneticGloss(
                        [
                            Reading.of_name("mu"),
                            Joiner.hyphen(),
                            Reading.of_name("ru"),
                            Joiner.hyphen(),
                            Reading.of_name("ub"),
                        ]
                    ),
                ],
            ),
        ),
        (
            "{+mu-ru-ub}[LA",
            Word(
                parts=[
                    PhoneticGloss(
                        [
                            Reading.of_name("mu"),
                            Joiner.hyphen(),
                            Reading.of_name("ru"),
                            Joiner.hyphen(),
                            Reading.of_name("ub"),
                        ]
                    ),
                    BrokenAway.open(),
                    Logogram.of_name("LA"),
                ],
            ),
        ),
        (
            "I.{d}",
            Word(
                parts=[
                    Logogram.of_name("I"),
                    Joiner.dot(),
                    Determinative([Reading.of_name("d")]),
                ],
            ),
        ),
        (
            "{d}[UTU?",
            Word(
                parts=[
                    Determinative([Reading.of_name("d")]),
                    BrokenAway.open(),
                    Logogram.of_name("UTU", flags=[atf.Flag.UNCERTAIN]),
                ],
            ),
        ),
        (
            ".x.KAM",
            Word(
                parts=[
                    Joiner.dot(),
                    UnclearSign(),
                    Joiner.dot(),
                    Logogram.of_name("KAM"),
                ],
            ),
        ),
        (
            "3.AM₃",
            Word(
                parts=[Number.of_name("3"), Joiner.dot(), Logogram.of_name("AM", 3),],
            ),
        ),
        (
            "<{10}>bu",
            Word(
                parts=[
                    AccidentalOmission.open(),
                    Determinative([Number.of_name("10")]),
                    AccidentalOmission.close(),
                    Reading.of_name("bu"),
                ],
            ),
        ),
        (
            "KA₂?].DINGIR.RA[{ki?}",
            Word(
                parts=[
                    Logogram.of_name("KA", 2, flags=[atf.Flag.UNCERTAIN]),
                    BrokenAway.close(),
                    Joiner.dot(),
                    Logogram.of_name("DINGIR"),
                    Joiner.dot(),
                    Logogram.of_name("RA"),
                    BrokenAway.open(),
                    Determinative([Reading.of_name("ki", flags=[atf.Flag.UNCERTAIN])]),
                ],
            ),
        ),
        (
            "{d?}nu?-di]m₂?-mu[d?",
            Word(
                parts=[
                    Determinative([Reading.of_name("d", flags=[atf.Flag.UNCERTAIN])]),
                    Reading.of_name("nu", flags=[atf.Flag.UNCERTAIN]),
                    Joiner.hyphen(),
                    Reading.of(
                        (ValueToken("di"), BrokenAway.close(), ValueToken("m")),
                        2,
                        flags=[atf.Flag.UNCERTAIN],
                    ),
                    Joiner.hyphen(),
                    Reading.of(
                        (ValueToken("mu"), BrokenAway.open(), ValueToken("d")),
                        flags=[atf.Flag.UNCERTAIN],
                    ),
                ],
            ),
        ),
        (
            "<GAR?>",
            Word(
                parts=[
                    AccidentalOmission.open(),
                    Logogram.of_name("GAR", flags=[atf.Flag.UNCERTAIN]),
                    AccidentalOmission.close(),
                ],
            ),
        ),
        (
            "<<GAR>>",
            Word(parts=[Removal.open(), Logogram.of_name("GAR"), Removal.close(),],),
        ),
        ("lu₂@v", Word(parts=[Reading.of_name("lu", 2, modifiers=["@v"])]),),
        (
            "{lu₂@v}UM.ME.[A",
            Word(
                parts=[
                    Determinative([Reading.of_name("lu", 2, modifiers=["@v"])]),
                    Logogram.of_name("UM"),
                    Joiner.dot(),
                    Logogram.of_name("ME"),
                    Joiner.dot(),
                    BrokenAway.open(),
                    Logogram.of_name("A"),
                ],
            ),
        ),
        (
            "{lu₂@v}]KAB.SAR-M[EŠ",
            Word(
                parts=[
                    Determinative([Reading.of_name("lu", 2, modifiers=["@v"])]),
                    BrokenAway.close(),
                    Logogram.of_name("KAB"),
                    Joiner.dot(),
                    Logogram.of_name("SAR"),
                    Joiner.hyphen(),
                    Logogram.of((ValueToken("M"), BrokenAway.open(), ValueToken("EŠ"))),
                ],
            ),
        ),
        (
            "MIN<(ta-ne₂-hi)>",
            Word(
                parts=[
                    Logogram.of_name(
                        "MIN",
                        surrogate=[
                            Reading.of_name("ta"),
                            Joiner.hyphen(),
                            Reading.of_name("ne", 2),
                            Joiner.hyphen(),
                            Reading.of_name("hi"),
                        ],
                    )
                ],
            ),
        ),
        (
            "MIN<(mu-u₂)>",
            Word(
                parts=[
                    Logogram.of_name(
                        "MIN",
                        surrogate=[
                            Reading.of_name("mu"),
                            Joiner.hyphen(),
                            Reading.of_name("u", 2),
                        ],
                    )
                ],
            ),
        ),
        (
            "KIMIN<(mu-u₂)>",
            Word(
                parts=[
                    Logogram.of_name(
                        "KIMIN",
                        surrogate=[
                            Reading.of_name("mu"),
                            Joiner.hyphen(),
                            Reading.of_name("u", 2),
                        ],
                    )
                ],
            ),
        ),
        ("UN#", Word(parts=[Logogram.of_name("UN", flags=[atf.Flag.DAMAGE])])),
        (
            "he₂-<(pa₃)>",
            Word(
                parts=[
                    Reading.of_name("he", 2),
                    Joiner.hyphen(),
                    IntentionalOmission.open(),
                    Reading.of_name("pa", 3),
                    IntentionalOmission.close(),
                ],
            ),
        ),
        (
            "[{i]ti}AB",
            Word(
                parts=[
                    BrokenAway.open(),
                    Determinative(
                        [
                            Reading.of(
                                (ValueToken("i"), BrokenAway.close(), ValueToken("ti"))
                            ),
                        ]
                    ),
                    Logogram.of_name("AB"),
                ],
            ),
        ),
        (
            "in]-",
            Word(parts=[Reading.of_name("in"), BrokenAway.close(), Joiner.hyphen(),],),
        ),
        (
            "<en-da-ab>",
            Word(
                parts=[
                    AccidentalOmission.open(),
                    Reading.of_name("en"),
                    Joiner.hyphen(),
                    Reading.of_name("da"),
                    Joiner.hyphen(),
                    Reading.of_name("ab"),
                    AccidentalOmission.close(),
                ],
            ),
        ),
        (
            "me-e-li-°\\ku°",
            Word(
                parts=[
                    Reading.of_name("me"),
                    Joiner.hyphen(),
                    Reading.of_name("e"),
                    Joiner.hyphen(),
                    Reading.of_name("li"),
                    Joiner.hyphen(),
                    Erasure.open(),
                    Erasure.center(),
                    Reading.of_name("ku"),
                    Erasure.close(),
                ],
            ),
        ),
        (
            "°me-e-li\\°-ku",
            Word(
                parts=[
                    Erasure.open(),
                    Reading.of_name("me"),
                    Joiner.hyphen(),
                    Reading.of_name("e"),
                    Joiner.hyphen(),
                    Reading.of_name("li"),
                    Erasure.center(),
                    Erasure.close(),
                    Joiner.hyphen(),
                    Reading.of_name("ku"),
                ],
            ),
        ),
        (
            "me-°e\\li°-ku",
            Word(
                parts=[
                    Reading.of_name("me"),
                    Joiner(atf.Joiner.HYPHEN),
                    Erasure.open(),
                    Reading.of_name("e"),
                    Erasure.center(),
                    Reading.of_name("li"),
                    Erasure.close(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("ku"),
                ],
            ),
        ),
        (
            "me-°e\\li°-me-°e\\li°-ku",
            Word(
                parts=[
                    Reading.of_name("me"),
                    Joiner(atf.Joiner.HYPHEN),
                    Erasure.open(),
                    Reading.of_name("e"),
                    Erasure.center(),
                    Reading.of_name("li"),
                    Erasure.close(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("me"),
                    Joiner(atf.Joiner.HYPHEN),
                    Erasure.open(),
                    Reading.of_name("e"),
                    Erasure.center(),
                    Reading.of_name("li"),
                    Erasure.close(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("ku"),
                ],
            ),
        ),
        (
            "...{d}kur",
            Word(
                parts=[
                    UnknownNumberOfSigns(),
                    Determinative([Reading.of_name("d")]),
                    Reading.of_name("kur"),
                ],
            ),
        ),
        (
            "kur{d}...",
            Word(
                parts=[
                    Reading.of_name("kur"),
                    Determinative([Reading.of_name("d")]),
                    UnknownNumberOfSigns(),
                ],
            ),
        ),
        (
            "...-kur-...",
            Word(
                parts=[
                    UnknownNumberOfSigns(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("kur"),
                    Joiner(atf.Joiner.HYPHEN),
                    UnknownNumberOfSigns(),
                ],
            ),
        ),
        (
            "kur-...-kur-...-kur",
            Word(
                parts=[
                    Reading.of_name("kur"),
                    Joiner(atf.Joiner.HYPHEN),
                    UnknownNumberOfSigns(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("kur"),
                    Joiner(atf.Joiner.HYPHEN),
                    UnknownNumberOfSigns(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("kur"),
                ],
            ),
        ),
        (
            "...]-ku",
            Word(
                parts=[
                    UnknownNumberOfSigns(),
                    BrokenAway.close(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("ku"),
                ],
            ),
        ),
        (
            "ku-[...",
            Word(
                parts=[
                    Reading.of_name("ku"),
                    Joiner(atf.Joiner.HYPHEN),
                    BrokenAway.open(),
                    UnknownNumberOfSigns(),
                ],
            ),
        ),
        (
            "....ku",
            Word(parts=[UnknownNumberOfSigns(), Joiner.dot(), Reading.of_name("ku"),],),
        ),
        (
            "ku....",
            Word(parts=[Reading.of_name("ku"), Joiner.dot(), UnknownNumberOfSigns(),],),
        ),
        (
            "(x)]",
            Word(
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
                parts=[
                    BrokenAway.open(),
                    Determinative([Reading.of_name("d")]),
                    Logogram.of_name("UTU"),
                ],
            ),
        ),
        (
            "{m#}[{d}AG-sa-lim",
            Word(
                parts=[
                    Determinative([Reading.of_name("m", flags=[atf.Flag.DAMAGE])]),
                    BrokenAway.open(),
                    Determinative([Reading.of_name("d")]),
                    Logogram.of_name("AG"),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("sa"),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("lim"),
                ],
            ),
        ),
        (
            "ša#-[<(mu-un-u₅)>]",
            Word(
                parts=[
                    Reading.of_name("ša", flags=[atf.Flag.DAMAGE]),
                    Joiner(atf.Joiner.HYPHEN),
                    BrokenAway.open(),
                    IntentionalOmission.open(),
                    Reading.of_name("mu"),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("un"),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("u", 5),
                    IntentionalOmission.close(),
                    BrokenAway.close(),
                ],
            ),
        ),
        (
            "|UM×(ME.DA)|-b[i?",
            Word(
                parts=[
                    CompoundGrapheme("|UM×(ME.DA)|"),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of(
                        (ValueToken("b"), BrokenAway.open(), ValueToken("i")),
                        flags=[atf.Flag.UNCERTAIN],
                    ),
                ],
            ),
        ),
        (
            "mu-un;-e₃",
            Word(
                parts=[
                    Reading.of_name("mu"),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("un"),
                    InWordNewline(),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("e", 3),
                ],
            ),
        ),
        (
            "du₃-am₃{{mu-un-<(du₃)>}}",
            Word(
                parts=[
                    Reading.of_name("du", 3),
                    Joiner(atf.Joiner.HYPHEN),
                    Reading.of_name("am", 3),
                    LinguisticGloss(
                        [
                            Reading.of_name("mu"),
                            Joiner(atf.Joiner.HYPHEN),
                            Reading.of_name("un"),
                            Joiner(atf.Joiner.HYPHEN),
                            IntentionalOmission.open(),
                            Reading.of_name("du", 3),
                            IntentionalOmission.close(),
                        ]
                    ),
                ],
            ),
        ),
        ("kurₓ", Word(parts=[Reading.of_name("kur", None),]),),
        ("KURₓ", Word(parts=[Logogram.of_name("KUR", None),]),),
        (
            "kurₓ(KUR)",
            Word(parts=[Reading.of_name("kur", None, sign=Grapheme.of("KUR")),],),
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
                parts=[
                    AccidentalOmission.open(),
                    Determinative([Number.of_name("10")]),
                    AccidentalOmission.close(),
                ],
            ),
        ),
        (
            "{ud]u?}",
            LoneDeterminative(
                parts=[
                    Determinative(
                        [
                            Reading.of(
                                (ValueToken("ud"), BrokenAway.close(), ValueToken("u")),
                                flags=[atf.Flag.UNCERTAIN],
                            )
                        ]
                    ),
                ],
            ),
        ),
        (
            "{u₂#}",
            LoneDeterminative(
                parts=[
                    Determinative([Reading.of_name("u", 2, flags=[atf.Flag.DAMAGE])]),
                ],
            ),
        ),
        (
            "{lu₂@v}",
            LoneDeterminative(
                parts=[Determinative([Reading.of_name("lu", 2, modifiers=["@v"])]),],
            ),
        ),
        (
            "{k[i}]",
            LoneDeterminative(
                parts=[
                    Determinative(
                        [
                            Reading.of(
                                (ValueToken("k"), BrokenAway.open(), ValueToken("i"))
                            ),
                        ]
                    ),
                    BrokenAway.close(),
                ],
            ),
        ),
        (
            "[{k]i}",
            LoneDeterminative(
                parts=[
                    BrokenAway.open(),
                    Determinative(
                        [
                            Reading.of(
                                (ValueToken("k"), BrokenAway.close(), ValueToken("i"))
                            ),
                        ]
                    ),
                ],
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
