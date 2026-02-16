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
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_word
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
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import (
    ErasureState,
    InWordNewline,
    LoneDeterminative,
    Word,
)


@pytest.mark.parametrize(
    "atf,expected",
    [
        ("...", Word.of([UnknownNumberOfSigns.of()])),
        ("x", Word.of([UnclearSign.of()])),
        ("X", Word.of([UnidentifiedSign.of()])),
        ("x?", Word.of([UnclearSign.of([atf.Flag.UNCERTAIN])])),
        ("X#", Word.of([UnidentifiedSign.of([atf.Flag.DAMAGE])])),
        ("12", Word.of([Number.of_name("12")])),
        (
            "1]2",
            Word.of(
                [
                    Number.of(
                        (ValueToken.of("1"), BrokenAway.close(), ValueToken.of("2"))
                    )
                ]
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
            Word.of(
                [LinguisticGloss.of([Reading.of_name("ku")]), Reading.of_name("nu")]
            ),
        ),
        (
            "ku{{nu}}",
            Word.of(
                [Reading.of_name("ku"), LinguisticGloss.of([Reading.of_name("nu")])]
            ),
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
        (
            "i-le-ʾe-[e",
            Word.of(
                [
                    Reading.of_name("i"),
                    Joiner.hyphen(),
                    Reading.of_name("le"),
                    Joiner.hyphen(),
                    Reading.of_name("ʾe"),
                    Joiner.hyphen(),
                    BrokenAway.open(),
                    Reading.of_name("e"),
                ]
            ),
        ),
        (
            "U₄.27/29.KAM",
            Word.of(
                [
                    Logogram.of_name("U", 4),
                    Joiner.dot(),
                    Variant.of(Number.of_name("27"), Number.of_name("29")),
                    Joiner.dot(),
                    Logogram.of_name("KAM"),
                ]
            ),
        ),
        (
            "x/m[a",
            Word.of(
                [
                    Variant.of(
                        UnclearSign.of(),
                        Reading.of(
                            (ValueToken.of("m"), BrokenAway.open(), ValueToken.of("a"))
                        ),
                    )
                ]
            ),
        ),
        (
            "SAL.{+mu-ru-ub}",
            Word.of(
                [
                    Logogram.of_name("SAL"),
                    Joiner.dot(),
                    PhoneticGloss.of(
                        [
                            Reading.of_name("mu"),
                            Joiner.hyphen(),
                            Reading.of_name("ru"),
                            Joiner.hyphen(),
                            Reading.of_name("ub"),
                        ]
                    ),
                ]
            ),
        ),
        (
            "{+mu-ru-ub}[LA",
            Word.of(
                [
                    PhoneticGloss.of(
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
                ]
            ),
        ),
        (
            "I.{d}",
            Word.of(
                [
                    Logogram.of_name("I"),
                    Joiner.dot(),
                    Determinative.of([Reading.of_name("d")]),
                ]
            ),
        ),
        (
            "{d}[UTU?",
            Word.of(
                [
                    Determinative.of([Reading.of_name("d")]),
                    BrokenAway.open(),
                    Logogram.of_name("UTU", flags=[atf.Flag.UNCERTAIN]),
                ]
            ),
        ),
        (
            "3.AM₃",
            Word.of([Number.of_name("3"), Joiner.dot(), Logogram.of_name("AM", 3)]),
        ),
        (
            "<{10}>bu",
            Word.of(
                [
                    AccidentalOmission.open(),
                    Determinative.of([Number.of_name("10")]),
                    AccidentalOmission.close(),
                    Reading.of_name("bu"),
                ]
            ),
        ),
        (
            "KA₂?].DINGIR.RA[{ki?}",
            Word.of(
                [
                    Logogram.of_name("KA", 2, flags=[atf.Flag.UNCERTAIN]),
                    BrokenAway.close(),
                    Joiner.dot(),
                    Logogram.of_name("DINGIR"),
                    Joiner.dot(),
                    Logogram.of_name("RA"),
                    BrokenAway.open(),
                    Determinative.of(
                        [Reading.of_name("ki", flags=[atf.Flag.UNCERTAIN])]
                    ),
                ]
            ),
        ),
        (
            "{d?}nu?-di]m₂?-mu[d?",
            Word.of(
                [
                    Determinative.of(
                        [Reading.of_name("d", flags=[atf.Flag.UNCERTAIN])]
                    ),
                    Reading.of_name("nu", flags=[atf.Flag.UNCERTAIN]),
                    Joiner.hyphen(),
                    Reading.of(
                        (ValueToken.of("di"), BrokenAway.close(), ValueToken.of("m")),
                        2,
                        flags=[atf.Flag.UNCERTAIN],
                    ),
                    Joiner.hyphen(),
                    Reading.of(
                        (ValueToken.of("mu"), BrokenAway.open(), ValueToken.of("d")),
                        flags=[atf.Flag.UNCERTAIN],
                    ),
                ]
            ),
        ),
        (
            "<GAR?>",
            Word.of(
                [
                    AccidentalOmission.open(),
                    Logogram.of_name("GAR", flags=[atf.Flag.UNCERTAIN]),
                    AccidentalOmission.close(),
                ]
            ),
        ),
        (
            "<<GAR>>",
            Word.of([Removal.open(), Logogram.of_name("GAR"), Removal.close()]),
        ),
        ("lu₂@v", Word.of([Reading.of_name("lu", 2, modifiers=["@v"])])),
        (
            "{lu₂@v}UM.ME.[A",
            Word.of(
                [
                    Determinative.of([Reading.of_name("lu", 2, modifiers=["@v"])]),
                    Logogram.of_name("UM"),
                    Joiner.dot(),
                    Logogram.of_name("ME"),
                    Joiner.dot(),
                    BrokenAway.open(),
                    Logogram.of_name("A"),
                ]
            ),
        ),
        (
            "{lu₂@v}]KAB.SAR-M[EŠ",
            Word.of(
                [
                    Determinative.of([Reading.of_name("lu", 2, modifiers=["@v"])]),
                    BrokenAway.close(),
                    Logogram.of_name("KAB"),
                    Joiner.dot(),
                    Logogram.of_name("SAR"),
                    Joiner.hyphen(),
                    Logogram.of(
                        (ValueToken.of("M"), BrokenAway.open(), ValueToken.of("EŠ"))
                    ),
                ]
            ),
        ),
        (
            "MIN<(ta-ne₂-hi)>",
            Word.of(
                [
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
                ]
            ),
        ),
        (
            "MIN<(mu-u₂)>",
            Word.of(
                [
                    Logogram.of_name(
                        "MIN",
                        surrogate=[
                            Reading.of_name("mu"),
                            Joiner.hyphen(),
                            Reading.of_name("u", 2),
                        ],
                    )
                ]
            ),
        ),
        (
            "KIMIN<(mu-u₂)>",
            Word.of(
                [
                    Logogram.of_name(
                        "KIMIN",
                        surrogate=[
                            Reading.of_name("mu"),
                            Joiner.hyphen(),
                            Reading.of_name("u", 2),
                        ],
                    )
                ]
            ),
        ),
        ("UN#", Word.of([Logogram.of_name("UN", flags=[atf.Flag.DAMAGE])])),
        (
            "he₂-<(pa₃)>",
            Word.of(
                [
                    Reading.of_name("he", 2),
                    Joiner.hyphen(),
                    IntentionalOmission.open(),
                    Reading.of_name("pa", 3),
                    IntentionalOmission.close(),
                ]
            ),
        ),
        (
            "[{i]ti}AB",
            Word.of(
                [
                    BrokenAway.open(),
                    Determinative.of(
                        [
                            Reading.of(
                                (
                                    ValueToken.of("i"),
                                    BrokenAway.close(),
                                    ValueToken.of("ti"),
                                )
                            )
                        ]
                    ),
                    Logogram.of_name("AB"),
                ]
            ),
        ),
        ("in]", Word.of([Reading.of_name("in"), BrokenAway.close()])),
        (
            "<en-da-ab>",
            Word.of(
                [
                    AccidentalOmission.open(),
                    Reading.of_name("en"),
                    Joiner.hyphen(),
                    Reading.of_name("da"),
                    Joiner.hyphen(),
                    Reading.of_name("ab"),
                    AccidentalOmission.close(),
                ]
            ),
        ),
        (
            "me-e-li-°\\ku°",
            Word.of(
                [
                    Reading.of_name("me"),
                    Joiner.hyphen(),
                    Reading.of_name("e"),
                    Joiner.hyphen(),
                    Reading.of_name("li"),
                    Joiner.hyphen(),
                    Erasure.open(),
                    Erasure.center(),
                    Reading.of_name("ku").set_erasure(ErasureState.OVER_ERASED),
                    Erasure.close(),
                ]
            ),
        ),
        (
            "°me-e-li\\°-ku",
            Word.of(
                [
                    Erasure.open(),
                    Reading.of_name("me").set_erasure(ErasureState.ERASED),
                    Joiner.hyphen().set_erasure(ErasureState.ERASED),
                    Reading.of_name("e").set_erasure(ErasureState.ERASED),
                    Joiner.hyphen().set_erasure(ErasureState.ERASED),
                    Reading.of_name("li").set_erasure(ErasureState.ERASED),
                    Erasure.center(),
                    Erasure.close(),
                    Joiner.hyphen(),
                    Reading.of_name("ku"),
                ]
            ),
        ),
        (
            "me-°e\\li°-ku",
            Word.of(
                [
                    Reading.of_name("me"),
                    Joiner.hyphen(),
                    Erasure.open(),
                    Reading.of_name("e").set_erasure(ErasureState.ERASED),
                    Erasure.center(),
                    Reading.of_name("li").set_erasure(ErasureState.OVER_ERASED),
                    Erasure.close(),
                    Joiner.hyphen(),
                    Reading.of_name("ku"),
                ]
            ),
        ),
        (
            "me-°e\\li°-me-°e\\li°-ku",
            Word.of(
                [
                    Reading.of_name("me"),
                    Joiner.hyphen(),
                    Erasure.open(),
                    Reading.of_name("e").set_erasure(ErasureState.ERASED),
                    Erasure.center(),
                    Reading.of_name("li").set_erasure(ErasureState.OVER_ERASED),
                    Erasure.close(),
                    Joiner.hyphen(),
                    Reading.of_name("me"),
                    Joiner.hyphen(),
                    Erasure.open(),
                    Reading.of_name("e").set_erasure(ErasureState.ERASED),
                    Erasure.center(),
                    Reading.of_name("li").set_erasure(ErasureState.OVER_ERASED),
                    Erasure.close(),
                    Joiner.hyphen(),
                    Reading.of_name("ku"),
                ]
            ),
        ),
        (
            "...{d}kur",
            Word.of(
                [
                    UnknownNumberOfSigns.of(),
                    Determinative.of([Reading.of_name("d")]),
                    Reading.of_name("kur"),
                ]
            ),
        ),
        (
            "kur{d}...",
            Word.of(
                [
                    Reading.of_name("kur"),
                    Determinative.of([Reading.of_name("d")]),
                    UnknownNumberOfSigns.of(),
                ]
            ),
        ),
        (
            "...-kur-...",
            Word.of(
                [
                    UnknownNumberOfSigns.of(),
                    Joiner.hyphen(),
                    Reading.of_name("kur"),
                    Joiner.hyphen(),
                    UnknownNumberOfSigns.of(),
                ]
            ),
        ),
        (
            "kur-...-kur-...-kur",
            Word.of(
                [
                    Reading.of_name("kur"),
                    Joiner.hyphen(),
                    UnknownNumberOfSigns.of(),
                    Joiner.hyphen(),
                    Reading.of_name("kur"),
                    Joiner.hyphen(),
                    UnknownNumberOfSigns.of(),
                    Joiner.hyphen(),
                    Reading.of_name("kur"),
                ]
            ),
        ),
        (
            "...]-ku",
            Word.of(
                [
                    UnknownNumberOfSigns.of(),
                    BrokenAway.close(),
                    Joiner.hyphen(),
                    Reading.of_name("ku"),
                ]
            ),
        ),
        (
            "ku-[...",
            Word.of(
                [
                    Reading.of_name("ku"),
                    Joiner.hyphen(),
                    BrokenAway.open(),
                    UnknownNumberOfSigns.of(),
                ]
            ),
        ),
        (
            "....ku",
            Word.of([UnknownNumberOfSigns.of(), Joiner.dot(), Reading.of_name("ku")]),
        ),
        (
            "ku....",
            Word.of([Reading.of_name("ku"), Joiner.dot(), UnknownNumberOfSigns.of()]),
        ),
        (
            "(x)]",
            Word.of(
                [
                    PerhapsBrokenAway.open(),
                    UnclearSign.of(),
                    PerhapsBrokenAway.close(),
                    BrokenAway.close(),
                ]
            ),
        ),
        (
            "[{d}UTU",
            Word.of(
                [
                    BrokenAway.open(),
                    Determinative.of([Reading.of_name("d")]),
                    Logogram.of_name("UTU"),
                ]
            ),
        ),
        (
            "{m#}[{d}AG-sa-lim",
            Word.of(
                [
                    Determinative.of([Reading.of_name("m", flags=[atf.Flag.DAMAGE])]),
                    BrokenAway.open(),
                    Determinative.of([Reading.of_name("d")]),
                    Logogram.of_name("AG"),
                    Joiner.hyphen(),
                    Reading.of_name("sa"),
                    Joiner.hyphen(),
                    Reading.of_name("lim"),
                ]
            ),
        ),
        (
            "ša#-[<(mu-un-u₅)>]",
            Word.of(
                [
                    Reading.of_name("ša", flags=[atf.Flag.DAMAGE]),
                    Joiner.hyphen(),
                    BrokenAway.open(),
                    IntentionalOmission.open(),
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("un"),
                    Joiner.hyphen(),
                    Reading.of_name("u", 5),
                    IntentionalOmission.close(),
                    BrokenAway.close(),
                ]
            ),
        ),
        (
            "|UM×(ME.DA)|-b[i?",
            Word.of(
                [
                    CompoundGrapheme.of(["UM×(ME.DA)"]),
                    Joiner.hyphen(),
                    Reading.of(
                        (ValueToken.of("b"), BrokenAway.open(), ValueToken.of("i")),
                        flags=[atf.Flag.UNCERTAIN],
                    ),
                ]
            ),
        ),
        (
            "mu-un;-e₃",
            Word.of(
                [
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("un"),
                    InWordNewline.of(),
                    Joiner.hyphen(),
                    Reading.of_name("e", 3),
                ]
            ),
        ),
        (
            "du₃-am₃{{mu-un-<(du₃)>}}",
            Word.of(
                [
                    Reading.of_name("du", 3),
                    Joiner.hyphen(),
                    Reading.of_name("am", 3),
                    LinguisticGloss.of(
                        [
                            Reading.of_name("mu"),
                            Joiner.hyphen(),
                            Reading.of_name("un"),
                            Joiner.hyphen(),
                            IntentionalOmission.open(),
                            Reading.of_name("du", 3),
                            IntentionalOmission.close(),
                        ]
                    ),
                ]
            ),
        ),
        ("kurₓ", Word.of([Reading.of_name("kur", None)])),
        ("KURₓ", Word.of([Logogram.of_name("KUR", None)])),
        (
            "kurₓ(KUR)",
            Word.of([Reading.of_name("kur", None, sign=Grapheme.of(SignName("KUR")))]),
        ),
    ],
)
def test_word(atf, expected) -> None:
    assert parse_word(atf) == expected


@pytest.mark.parametrize(
    "atf,expected",
    [
        (
            "<{10}>",
            LoneDeterminative.of(
                [
                    AccidentalOmission.open(),
                    Determinative.of([Number.of_name("10")]),
                    AccidentalOmission.close(),
                ]
            ),
        ),
        (
            "{ud]u?}",
            LoneDeterminative.of(
                [
                    Determinative.of(
                        [
                            Reading.of(
                                (
                                    ValueToken.of("ud"),
                                    BrokenAway.close(),
                                    ValueToken.of("u"),
                                ),
                                flags=[atf.Flag.UNCERTAIN],
                            )
                        ]
                    )
                ]
            ),
        ),
        (
            "{u₂#}",
            LoneDeterminative.of(
                [Determinative.of([Reading.of_name("u", 2, flags=[atf.Flag.DAMAGE])])]
            ),
        ),
        (
            "{lu₂@v}",
            LoneDeterminative.of(
                [Determinative.of([Reading.of_name("lu", 2, modifiers=["@v"])])]
            ),
        ),
        (
            "{k[i}]",
            LoneDeterminative.of(
                [
                    Determinative.of(
                        [
                            Reading.of(
                                (
                                    ValueToken.of("k"),
                                    BrokenAway.open(),
                                    ValueToken.of("i"),
                                )
                            )
                        ]
                    ),
                    BrokenAway.close(),
                ]
            ),
        ),
        (
            "[{k]i}",
            LoneDeterminative.of(
                [
                    BrokenAway.open(),
                    Determinative.of(
                        [
                            Reading.of(
                                (
                                    ValueToken.of("k"),
                                    BrokenAway.close(),
                                    ValueToken.of("i"),
                                )
                            )
                        ]
                    ),
                ]
            ),
        ),
    ],
)
def test_lone_determinative(atf, expected) -> None:
    assert parse_word(atf) == expected


@pytest.mark.parametrize("atf", ["{udu}?"])
def test_invalid_lone_determinative(atf) -> None:
    with pytest.raises(UnexpectedInput):
        parse_word(atf)


@pytest.mark.parametrize(
    "invalid_atf",
    [
        "Kur",
        "ku(r",
        "K)UR",
        "K[(UR",
        "ku)]r",
        "sal/: šim",
        "<GAR>?",
        "KA₂]?.DINGIR.RA[{ki?}",
        "KA₂?].DINGIR.RA[{ki}?",
        "k[a]?",
        ":-sal",
        "gam/://sal",
        "Š[A₃?...]",
        "|KU]R|",
        "|KUR.[KUR|",
        "-kur",
        "kur-",
        "]-kur",
        "kur-[",
    ],
)
def test_invalid(invalid_atf) -> None:
    with pytest.raises((UnexpectedInput, ParseError)):
        parse_word(invalid_atf)
