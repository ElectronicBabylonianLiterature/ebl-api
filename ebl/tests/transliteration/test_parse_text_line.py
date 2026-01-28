from typing import List

import pytest
from hamcrest import starts_with

from ebl.tests.assertions import assert_exception_has_errors
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    Determinative,
    DocumentOrientedGloss,
    Erasure,
    IntentionalOmission,
    PerhapsBrokenAway,
    Removal,
)
from ebl.transliteration.domain.greek_tokens import GreekLetter, GreekWord
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
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
    LineBreak,
    Tabulation,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import (
    ErasureState,
    InWordNewline,
    LoneDeterminative,
    Word,
)

DEFAULT_LANGUAGE = Language.AKKADIAN


def create_number_part(number: str) -> Number:
    return Number.of((ValueToken.of(number),))


@pytest.mark.parametrize(
    "parser,version", [(parse_atf_lark, f"{atf.ATF_PARSER_VERSION}")]
)
def test_parser_version(parser, version):
    assert parser("1. kur").parser_version == version


@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        (
            "1′. ...",
            [
                TextLine.of_iterable(
                    LineNumber(1, True), (Word.of((UnknownNumberOfSigns.of(),)),)
                )
            ],
        ),
        (
            "1’. ...",
            [
                TextLine.of_iterable(
                    LineNumber(1, True), (Word.of((UnknownNumberOfSigns.of(),)),)
                )
            ],
        ),
        (
            "D+113'a. ...",
            [
                TextLine.of_iterable(
                    LineNumber(113, True, "D", "a"),
                    (Word.of((UnknownNumberOfSigns.of(),)),),
                )
            ],
        ),
        (
            "z+113'a-9b. ...",
            [
                TextLine.of_iterable(
                    LineNumberRange(
                        LineNumber(113, True, "z", "a"), LineNumber(9, False, None, "b")
                    ),
                    (Word.of((UnknownNumberOfSigns.of(),)),),
                )
            ],
        ),
        ("1. ($___$)", [TextLine.of_iterable(LineNumber(1), (Tabulation.of(),))]),
        (
            "1. ... [...] [(...)]",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of((UnknownNumberOfSigns.of(),)),
                        Word.of(
                            (
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            )
                        ),
                        Word.of(
                            (
                                BrokenAway.open(),
                                PerhapsBrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                PerhapsBrokenAway.close(),
                                BrokenAway.close(),
                            )
                        ),
                    ),
                )
            ],
        ),
        (
            "1. [(x x x)]",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                PerhapsBrokenAway.open(),
                                UnclearSign.of(),
                            ]
                        ),
                        Word.of([UnclearSign.of()]),
                        Word.of(
                            parts=[
                                UnclearSign.of(),
                                PerhapsBrokenAway.close(),
                                BrokenAway.close(),
                            ]
                        ),
                    ),
                )
            ],
        ),
        (
            "1. <en-da-ab-su₈ ... >",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            parts=[
                                AccidentalOmission.open(),
                                Reading.of_name("en"),
                                Joiner.hyphen(),
                                Reading.of_name("da"),
                                Joiner.hyphen(),
                                Reading.of_name("ab"),
                                Joiner.hyphen(),
                                Reading.of_name("su", 8),
                            ]
                        ),
                        Word.of((UnknownNumberOfSigns.of(),)),
                        AccidentalOmission.close(),
                    ),
                )
            ],
        ),
        (
            "1. <<en ...>>",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of([Removal.open(), Reading.of_name("en")]),
                        Word.of((UnknownNumberOfSigns.of(), Removal.close())),
                    ),
                )
            ],
        ),
        (
            "1. & &12",
            [TextLine.of_iterable(LineNumber(1), (Column.of(), Column.of(12)))],
        ),
        (
            "1. | : :' :\" :. :: ; /",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        LineBreak.of(),
                        Divider.of(":"),
                        Divider.of(":'"),
                        Divider.of(':"'),
                        Divider.of(":."),
                        Divider.of("::"),
                        Divider.of(";"),
                        Divider.of("/"),
                    ),
                )
            ],
        ),
        (
            "1. ;/: :'/sal //: ://",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Variant.of(Divider.of(";"), Divider.of(":")),
                        Variant.of(Divider.of(":'"), Reading.of_name("sal")),
                        Variant.of(Divider.of("/"), Divider.of(":")),
                        Variant.of(Divider.of(":"), Divider.of("/")),
                    ),
                )
            ],
        ),
        (
            "1. me-e+li  me.e:li :\n2. ku",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            [
                                Reading.of_name("me"),
                                Joiner.hyphen(),
                                Reading.of_name("e"),
                                Joiner.plus(),
                                Reading.of_name("li"),
                            ]
                        ),
                        Word.of(
                            [
                                Reading.of_name("me"),
                                Joiner.dot(),
                                Reading.of_name("e"),
                                Joiner.colon(),
                                Reading.of_name("li"),
                            ]
                        ),
                        Divider.of(":"),
                    ),
                ),
                TextLine.of_iterable(
                    LineNumber(2), (Word.of([Reading.of_name("ku")]),)
                ),
            ],
        ),
        (
            "1. |GAL|",
            [
                TextLine.of_iterable(
                    LineNumber(1), (Word.of([CompoundGrapheme.of(["GAL"])]),)
                )
            ],
        ),
        (
            "1. !qt !bs !cm !zz",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        CommentaryProtocol.of("!qt"),
                        CommentaryProtocol.of("!bs"),
                        CommentaryProtocol.of("!cm"),
                        CommentaryProtocol.of("!zz"),
                    ),
                )
            ],
        ),
        (
            "1. x X x?# X#!",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of([UnclearSign.of()]),
                        Word.of([UnidentifiedSign.of()]),
                        Word.of(
                            [UnclearSign.of([atf.Flag.UNCERTAIN, atf.Flag.DAMAGE])]
                        ),
                        Word.of(
                            [
                                UnidentifiedSign.of(
                                    [atf.Flag.DAMAGE, atf.Flag.CORRECTION]
                                )
                            ]
                        ),
                    ),
                )
            ],
        ),
        (
            "1. x-ti ti-X",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            [UnclearSign.of(), Joiner.hyphen(), Reading.of_name("ti")]
                        ),
                        Word.of(
                            [
                                Reading.of_name("ti"),
                                Joiner.hyphen(),
                                UnidentifiedSign.of(),
                            ]
                        ),
                    ),
                )
            ],
        ),
        (
            "1. [... r]u?-u₂-qu na-a[n-...]\n2. ši-[ku-...-ku]-nu\n3. [...]-ku",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of((BrokenAway.open(), UnknownNumberOfSigns.of())),
                        Word.of(
                            parts=[
                                Reading.of(
                                    (
                                        ValueToken.of("r"),
                                        BrokenAway.close(),
                                        ValueToken.of("u"),
                                    ),
                                    flags=[atf.Flag.UNCERTAIN],
                                ),
                                Joiner.hyphen(),
                                Reading.of_name("u", 2),
                                Joiner.hyphen(),
                                Reading.of_name("qu"),
                            ]
                        ),
                        Word.of(
                            parts=[
                                Reading.of_name("na"),
                                Joiner.hyphen(),
                                Reading.of(
                                    (
                                        ValueToken.of("a"),
                                        BrokenAway.open(),
                                        ValueToken.of("n"),
                                    )
                                ),
                                Joiner.hyphen(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            ]
                        ),
                    ),
                ),
                TextLine.of_iterable(
                    LineNumber(2),
                    (
                        Word.of(
                            parts=[
                                Reading.of_name("ši"),
                                Joiner.hyphen(),
                                BrokenAway.open(),
                                Reading.of_name("ku"),
                                Joiner.hyphen(),
                                UnknownNumberOfSigns.of(),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                Reading.of_name("nu"),
                            ]
                        ),
                    ),
                ),
                TextLine.of_iterable(
                    LineNumber(3),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                            ]
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. [...]-qa-[...]-ba-[...]\n2. pa-[...]",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                Reading.of_name("qa"),
                                Joiner.hyphen(),
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                Reading.of_name("ba"),
                                Joiner.hyphen(),
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            ]
                        ),
                    ),
                ),
                TextLine.of_iterable(
                    LineNumber(2),
                    (
                        Word.of(
                            parts=[
                                Reading.of_name("pa"),
                                Joiner.hyphen(),
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            ]
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. [a?-ku (...)]\n2. [a?-ku (x)]",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                Reading.of_name("a", flags=[atf.Flag.UNCERTAIN]),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                            ]
                        ),
                        Word.of(
                            (
                                PerhapsBrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                PerhapsBrokenAway.close(),
                                BrokenAway.close(),
                            )
                        ),
                    ),
                ),
                TextLine.of_iterable(
                    LineNumber(2),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                Reading.of_name("a", flags=[atf.Flag.UNCERTAIN]),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                            ]
                        ),
                        Word.of(
                            parts=[
                                PerhapsBrokenAway.open(),
                                UnclearSign.of(),
                                PerhapsBrokenAway.close(),
                                BrokenAway.close(),
                            ]
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. [...+ku....] [....ku+...]",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                Joiner.plus(),
                                Reading.of_name("ku"),
                                Joiner.dot(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            ]
                        ),
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                Joiner.dot(),
                                Reading.of_name("ku"),
                                Joiner.plus(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            ]
                        ),
                    ),
                )
            ],
        ),
        (
            (
                "1. [...] {bu} [...]\n"
                "2. [...]{bu} [...]\n"
                "3. [...] {bu}[...]\n"
                "4. [...]{bu}[...]"
            ),
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            (
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            )
                        ),
                        LoneDeterminative.of_value(
                            [Determinative.of([Reading.of_name("bu")])],
                            ErasureState.NONE,
                        ),
                        Word.of(
                            (
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            )
                        ),
                    ),
                ),
                TextLine.of_iterable(
                    LineNumber(2),
                    (
                        Word.of(
                            [
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                                Determinative.of([Reading.of_name("bu")]),
                            ]
                        ),
                        Word.of(
                            (
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            )
                        ),
                    ),
                ),
                TextLine.of_iterable(
                    LineNumber(3),
                    (
                        Word.of(
                            (
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            )
                        ),
                        Word.of(
                            [
                                Determinative.of([Reading.of_name("bu")]),
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            ]
                        ),
                    ),
                ),
                TextLine.of_iterable(
                    LineNumber(4),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                                Determinative.of([Reading.of_name("bu")]),
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            ]
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. {bu}-nu {bu-bu}-nu\n2. {bu-bu}",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            parts=[
                                Determinative.of([Reading.of_name("bu")]),
                                Joiner.hyphen(),
                                Reading.of_name("nu"),
                            ]
                        ),
                        Word.of(
                            parts=[
                                Determinative.of(
                                    [
                                        Reading.of_name("bu"),
                                        Joiner.hyphen(),
                                        Reading.of_name("bu"),
                                    ]
                                ),
                                Joiner.hyphen(),
                                Reading.of_name("nu"),
                            ]
                        ),
                    ),
                ),
                TextLine.of_iterable(
                    LineNumber(2),
                    (
                        LoneDeterminative.of_value(
                            [
                                Determinative.of(
                                    [
                                        Reading.of_name("bu"),
                                        Joiner.hyphen(),
                                        Reading.of_name("bu"),
                                    ]
                                )
                            ],
                            ErasureState.NONE,
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. KIMIN {u₂#}[...] {u₂#} [...]",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of([Logogram.of_name("KIMIN")]),
                        Word.of(
                            parts=[
                                Determinative.of(
                                    [Reading.of_name("u", 2, flags=[atf.Flag.DAMAGE])]
                                ),
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            ]
                        ),
                        LoneDeterminative.of_value(
                            [
                                Determinative.of(
                                    [Reading.of_name("u", 2, flags=[atf.Flag.DAMAGE])]
                                )
                            ],
                            ErasureState.NONE,
                        ),
                        Word.of(
                            (
                                BrokenAway.open(),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            )
                        ),
                    ),
                )
            ],
        ),
        (
            "1. šu gid₂\n2. [U₄].14.KAM₂ U₄.15.KAM₂",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of([Reading.of_name("šu")]),
                        Word.of([Reading.of_name("gid", 2)]),
                    ),
                ),
                TextLine.of_iterable(
                    LineNumber(2),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                Logogram.of_name("U", 4),
                                BrokenAway.close(),
                                Joiner.dot(),
                                Number.of_name("14"),
                                Joiner.dot(),
                                Logogram.of_name("KAM", 2),
                            ]
                        ),
                        Word.of(
                            parts=[
                                Logogram.of_name("U", 4),
                                Joiner.dot(),
                                Number.of_name("15"),
                                Joiner.dot(),
                                Logogram.of_name("KAM", 2),
                            ]
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. {(he-pi₂ eš-šu₂)}\n2. {(NU SUR)}",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        DocumentOrientedGloss.open(),
                        Word.of(
                            parts=[
                                Reading.of_name("he"),
                                Joiner.hyphen(),
                                Reading.of_name("pi", 2),
                            ]
                        ),
                        Word.of(
                            parts=[
                                Reading.of_name("eš"),
                                Joiner.hyphen(),
                                Reading.of_name("šu", 2),
                            ]
                        ),
                        DocumentOrientedGloss.close(),
                    ),
                ),
                TextLine.of_iterable(
                    LineNumber(2),
                    (
                        DocumentOrientedGloss.open(),
                        Word.of([Logogram.of_name("NU")]),
                        Word.of([Logogram.of_name("SUR")]),
                        DocumentOrientedGloss.close(),
                    ),
                ),
            ],
        ),
        (
            "1.  sal/: šim ",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Variant.of(Reading.of_name("sal"), Divider.of(":")),
                        Word.of([Reading.of_name("šim")]),
                    ),
                )
            ],
        ),
        (
            "1. °me-e-li\\ku°",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Erasure.open(),
                        Word.of(
                            erasure=ErasureState.ERASED,
                            parts=[
                                Reading.of_name("me"),
                                Joiner.hyphen(),
                                Reading.of_name("e"),
                                Joiner.hyphen(),
                                Reading.of_name("li"),
                            ],
                        ),
                        Erasure.center(),
                        Word.of(
                            erasure=ErasureState.OVER_ERASED,
                            parts=[Reading.of_name("ku")],
                        ),
                        Erasure.close(),
                    ),
                )
            ],
        ),
        (
            "1. me-e-li-°\\ku°",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            parts=[
                                Reading.of_name("me"),
                                Joiner.hyphen(),
                                Reading.of_name("e"),
                                Joiner.hyphen(),
                                Reading.of_name("li"),
                                Joiner.hyphen(),
                                Erasure.open(),
                                Erasure.center(),
                                Reading.of_name("ku").set_erasure(
                                    ErasureState.OVER_ERASED
                                ),
                                Erasure.close(),
                            ]
                        ),
                    ),
                )
            ],
        ),
        (
            "1. °me-e-li\\°-ku",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            parts=[
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
                )
            ],
        ),
        (
            "1. me-°e\\li°-ku",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            parts=[
                                Reading.of_name("me"),
                                Joiner.hyphen(),
                                Erasure.open(),
                                Reading.of_name("e").set_erasure(ErasureState.ERASED),
                                Erasure.center(),
                                Reading.of_name("li").set_erasure(
                                    ErasureState.OVER_ERASED
                                ),
                                Erasure.close(),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                            ]
                        ),
                    ),
                )
            ],
        ),
        (
            "1. me-°e\\li°-me-°e\\li°-ku",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            parts=[
                                Reading.of_name("me"),
                                Joiner.hyphen(),
                                Erasure.open(),
                                Reading.of_name("e").set_erasure(ErasureState.ERASED),
                                Erasure.center(),
                                Reading.of_name("li").set_erasure(
                                    ErasureState.OVER_ERASED
                                ),
                                Erasure.close(),
                                Joiner.hyphen(),
                                Reading.of_name("me"),
                                Joiner.hyphen(),
                                Erasure.open(),
                                Reading.of_name("e").set_erasure(ErasureState.ERASED),
                                Erasure.center(),
                                Reading.of_name("li").set_erasure(
                                    ErasureState.OVER_ERASED
                                ),
                                Erasure.close(),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                            ]
                        ),
                    ),
                )
            ],
        ),
        (
            "1. [{(he-pi₂ e]š-šu₂)}",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        BrokenAway.open(),
                        DocumentOrientedGloss.open(),
                        Word.of(
                            parts=[
                                Reading.of_name("he"),
                                Joiner.hyphen(),
                                Reading.of_name("pi", 2),
                            ]
                        ),
                        Word.of(
                            parts=[
                                Reading.of(
                                    (
                                        ValueToken.of("e"),
                                        BrokenAway.close(),
                                        ValueToken.of("š"),
                                    )
                                ),
                                Joiner.hyphen(),
                                Reading.of_name("šu", 2),
                            ]
                        ),
                        DocumentOrientedGloss.close(),
                    ),
                )
            ],
        ),
        (
            "1. [{iti}...]",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                Determinative.of([Reading.of_name("iti")]),
                                UnknownNumberOfSigns.of(),
                                BrokenAway.close(),
                            ]
                        ),
                    ),
                )
            ],
        ),
        (
            "2. RA{k[i}]",
            [
                TextLine.of_iterable(
                    LineNumber(2),
                    (
                        Word.of(
                            parts=[
                                Logogram.of_name("RA"),
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
                )
            ],
        ),
        (
            "2. [in]-<(...)>",
            [
                TextLine.of_iterable(
                    LineNumber(2),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                Reading.of_name("in"),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                IntentionalOmission.open(),
                                UnknownNumberOfSigns.of(),
                                IntentionalOmission.close(),
                            ]
                        ),
                    ),
                )
            ],
        ),
        (
            "2. ...{d}kur ... {d}kur",
            [
                TextLine.of_iterable(
                    LineNumber(2),
                    (
                        Word.of(
                            parts=[
                                UnknownNumberOfSigns.of(),
                                Determinative.of([Reading.of_name("d")]),
                                Reading.of_name("kur"),
                            ]
                        ),
                        Word.of((UnknownNumberOfSigns.of(),)),
                        Word.of(
                            parts=[
                                Determinative.of([Reading.of_name("d")]),
                                Reading.of_name("kur"),
                            ]
                        ),
                    ),
                )
            ],
        ),
        (
            "2. kur{d}... kur{d} ...",
            [
                TextLine.of_iterable(
                    LineNumber(2),
                    (
                        Word.of(
                            parts=[
                                Reading.of_name("kur"),
                                Determinative.of([Reading.of_name("d")]),
                                UnknownNumberOfSigns.of(),
                            ]
                        ),
                        Word.of(
                            parts=[
                                Reading.of_name("kur"),
                                Determinative.of([Reading.of_name("d")]),
                            ]
                        ),
                        Word.of((UnknownNumberOfSigns.of(),)),
                    ),
                )
            ],
        ),
        (
            "1. mu-un;-e₃ ;",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            parts=[
                                Reading.of_name("mu"),
                                Joiner.hyphen(),
                                Reading.of_name("un"),
                                InWordNewline.of(),
                                Joiner.hyphen(),
                                Reading.of_name("e", 3),
                            ]
                        ),
                        Divider.of(";"),
                    ),
                )
            ],
        ),
        (
            "1. [... {(he-p]i₂)}",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of((BrokenAway.open(), UnknownNumberOfSigns.of())),
                        DocumentOrientedGloss.open(),
                        Word.of(
                            parts=[
                                Reading.of_name("he"),
                                Joiner.hyphen(),
                                Reading.of(
                                    (
                                        ValueToken.of("p"),
                                        BrokenAway.close(),
                                        ValueToken.of("i"),
                                    ),
                                    2,
                                ),
                            ]
                        ),
                        DocumentOrientedGloss.close(),
                    ),
                )
            ],
        ),
        (
            "1. ... -ad ad- ... ad- ... -ad",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        Word.of(
                            (
                                UnknownNumberOfSigns.of(),
                                Joiner.hyphen(),
                                Reading.of_name("ad"),
                            )
                        ),
                        Word.of(
                            (
                                Reading.of_name("ad"),
                                Joiner.hyphen(),
                                UnknownNumberOfSigns.of(),
                            )
                        ),
                        Word.of(
                            (
                                Reading.of_name("ad"),
                                Joiner.hyphen(),
                                UnknownNumberOfSigns.of(),
                                Joiner.hyphen(),
                                Reading.of_name("ad"),
                            )
                        ),
                    ),
                )
            ],
        ),
        (
            "1. %grc ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        LanguageShift.of("%grc"),
                        GreekWord.of(
                            [
                                GreekLetter.of(letter)
                                for letter in (
                                    "ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμ"
                                    "ΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω"
                                )
                            ]
                        ),
                    ),
                )
            ],
        ),
        (
            "1. %akkgrc α",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        LanguageShift.of("%akkgrc"),
                        GreekWord.of([GreekLetter.of("α")], Language.AKKADIAN),
                    ),
                )
            ],
        ),
        (
            "1. %suxgrc ε",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        LanguageShift.of("%suxgrc"),
                        GreekWord.of([GreekLetter.of("ε")], Language.SUMERIAN),
                    ),
                )
            ],
        ),
        (
            "1. %grc &2 α & ε",
            [
                TextLine.of_iterable(
                    LineNumber(1),
                    (
                        LanguageShift.of("%grc"),
                        Column.of(2),
                        GreekWord.of([GreekLetter.of("α")]),
                        Column.of(),
                        GreekWord.of([GreekLetter.of("ε")]),
                    ),
                )
            ],
        ),
        (
            "42. 1;23.45",
            [
                TextLine.of_iterable(
                    LineNumber(42),
                    (
                        Word.of(
                            [
                                create_number_part("1"),
                                Joiner.of(atf.Joiner.SEMICOLON),
                                create_number_part("23"),
                                Joiner.of(atf.Joiner.DOT),
                                create_number_part("45"),
                            ]
                        ),
                    ),
                )
            ],
        ),
    ],
)
def test_parse_text_line(line: str, expected_tokens: List[Line]) -> None:
    assert parse_atf_lark(line).lines == Text.of_iterable(expected_tokens).lines


def test_parse_dividers() -> None:
    line, expected_tokens = (
        r'1. :? :#! :# ::? :.@v /@19* :"@20@c ;@v@19!',
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Divider.of(":", (), (atf.Flag.UNCERTAIN,)),
                    Divider.of(":", (), (atf.Flag.DAMAGE, atf.Flag.CORRECTION)),
                    Divider.of(":", (), (atf.Flag.DAMAGE,)),
                    Divider.of("::", (), (atf.Flag.UNCERTAIN,)),
                    Divider.of(":.", ("@v",), ()),
                    Divider.of("/", ("@19",), (atf.Flag.COLLATION,)),
                    Divider.of(':"', ("@20", "@c"), ()),
                    Divider.of(";", ("@v", "@19"), (atf.Flag.CORRECTION,)),
                ),
            )
        ],
    )
    assert parse_atf_lark(line).lines == Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize(
    "code,expected_language",
    [
        ("%ma", Language.AKKADIAN),
        ("%mb", Language.AKKADIAN),
        ("%na", Language.AKKADIAN),
        ("%nb", Language.AKKADIAN),
        ("%lb", Language.AKKADIAN),
        ("%sb", Language.AKKADIAN),
        ("%a", Language.AKKADIAN),
        ("%akk", Language.AKKADIAN),
        ("%eakk", Language.AKKADIAN),
        ("%oakk", Language.AKKADIAN),
        ("%ur3akk", Language.AKKADIAN),
        ("%oa", Language.AKKADIAN),
        ("%ob", Language.AKKADIAN),
        ("%sux", Language.SUMERIAN),
        ("%es", Language.EMESAL),
        ("%hit", Language.HITTITE),
        ("%foo", DEFAULT_LANGUAGE),
    ],
)
def test_parse_atf_language_shifts(code: str, expected_language: Language) -> None:
    word = "ha-am"
    parts = [Reading.of_name("ha"), Joiner.hyphen(), Reading.of_name("am")]
    line = f"1. {word} {code} {word} %sb {word}"

    expected = Text(
        (
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(parts, DEFAULT_LANGUAGE),
                    LanguageShift.of(code),
                    Word.of(parts, expected_language),
                    LanguageShift.of("%sb"),
                    Word.of(parts, Language.AKKADIAN),
                ),
            ),
        )
    )

    assert parse_atf_lark(line).lines == expected.lines


def test_parse_normalized_akkadain_shift() -> None:
    word = "ha"
    line = f"1. {word} %n {word} %sux {word}"

    expected = Text(
        (
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of((Reading.of_name(word),), DEFAULT_LANGUAGE),
                    LanguageShift.normalized_akkadian(),
                    AkkadianWord.of((ValueToken.of(word),)),
                    LanguageShift.of("%sux"),
                    Word.of((Reading.of_name(word),), Language.SUMERIAN),
                ),
            ),
        )
    )

    assert parse_atf_lark(line).lines == expected.lines


@pytest.mark.parametrize(
    "atf,line_numbers",
    [
        ("1. x\nthis is not valid", [2]),
        ("1'. ($____$) x [...]\n$ (too many underscores)", [1]),
        ("1. me°-e\\li°-ku", [1]),
        ("1. me-°e\\li-°ku", [1]),
        ("1. {[me}]\n2. [{me]}\n3. {[me]}", [1, 2, 3]),
        ("a+1.a+2. šu", [1]),
    ],
)
def test_invalid_text_line(atf, line_numbers) -> None:
    with pytest.raises(TransliterationError) as exc_info:  # pyre-ignore[16]
        parse_atf_lark(atf)

    assert_exception_has_errors(exc_info, line_numbers, starts_with("Invalid line"))


@pytest.mark.parametrize(
    "atf,line_numbers", [("1. x\n2. [", [2]), ("1. [\n2. ]", [1, 2])]
)
def test_invalid_brackets(atf, line_numbers) -> None:
    with pytest.raises(TransliterationError) as exc_info:  # pyre-ignore[16]
        parse_atf_lark(atf)

    assert_exception_has_errors(exc_info, line_numbers, "Invalid brackets.")
