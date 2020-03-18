from typing import List

import pytest
from hamcrest import assert_that, contains_exactly, has_entries, starts_with

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import ScopeContainer, StateDollarLine
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
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line import ControlLine, EmptyLine, Line
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
    LanguageShift,
    LineContinuation,
    Tabulation,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.transliteration.domain.word_tokens import (
    ErasureState,
    InWordNewline,
    LoneDeterminative,
    Word,
)

DEFAULT_LANGUAGE = Language.AKKADIAN


@pytest.mark.parametrize(
    "parser,version", [(parse_atf_lark, f"{atf.ATF_PARSER_VERSION}")]
)
def test_parser_version(parser, version):
    assert parser("1. kur").parser_version == version


@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        ("", []),
        ("\n", []),
        (
            "#first\n\n#second",
            [
                ControlLine.of_single("#", ValueToken.of("first")),
                EmptyLine(),
                ControlLine.of_single("#", ValueToken.of("second")),
            ],
        ),
        (
            "#first\n \n#second",
            [
                ControlLine.of_single("#", ValueToken.of("first")),
                EmptyLine(),
                ControlLine.of_single("#", ValueToken.of("second")),
            ],
        ),
        ("&K11111", [ControlLine.of_single("&", ValueToken.of("K11111"))]),
        ("@reverse", [ControlLine.of_single("@", ValueToken.of("reverse"))]),
        (
            "$ (end of side)",
            [
                StateDollarLine(
                    None,
                    atf.Extent.END_OF,
                    ScopeContainer(atf.Scope.SIDE, ""),
                    None,
                    None,
                )
            ],
        ),
        ("#some notes", [ControlLine.of_single("#", ValueToken.of("some notes"))],),
        (
            "=: continuation",
            [ControlLine.of_single("=:", ValueToken.of(" continuation"))],
        ),
        (
            "a+1.a+2. šu",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("a+1.a+2."),
                    (Word.of([Reading.of_name("šu")]),),
                )
            ],
        ),
        (
            "1. ($___$)",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."), (Tabulation.of("($___$)"),)
                )
            ],
        ),
        (
            "1. ... [...] [(...)]",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        UnknownNumberOfSigns(frozenset()),
                        BrokenAway.open(),
                        UnknownNumberOfSigns(frozenset()),
                        BrokenAway.close(),
                        BrokenAway.open(),
                        PerhapsBrokenAway.open(),
                        UnknownNumberOfSigns(frozenset()),
                        PerhapsBrokenAway.close(),
                        BrokenAway.close(),
                    ),
                )
            ],
        ),
        (
            "1. [(x x x)]",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                PerhapsBrokenAway.open(),
                                UnclearSign(frozenset()),
                            ],
                        ),
                        Word.of([UnclearSign(frozenset())]),
                        Word.of(
                            parts=[
                                UnclearSign(frozenset()),
                                PerhapsBrokenAway.close(),
                                BrokenAway.close(),
                            ],
                        ),
                    ),
                )
            ],
        ),
        (
            "1. <en-da-ab-su₈ ... >",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
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
                            ],
                        ),
                        UnknownNumberOfSigns(frozenset()),
                        AccidentalOmission.close(),
                    ),
                )
            ],
        ),
        (
            "1. <<en ...>>",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of([Removal.open(), Reading.of_name("en"),]),
                        UnknownNumberOfSigns(frozenset()),
                        Removal.close(),
                    ),
                )
            ],
        ),
        (
            "1. & &12",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."), (Column.of(), Column.of(12))
                )
            ],
        ),
        (
            "1. | : :' :\" :. :: ; /",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Divider.of("|"),
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
            "1. |/: :'/sal //: ://",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Variant.of(Divider.of("|"), Divider.of(":")),
                        Variant.of(Divider.of(":'"), Reading.of_name("sal"),),
                        Variant.of(Divider.of("/"), Divider.of(":")),
                        Variant.of(Divider.of(":"), Divider.of("/")),
                    ),
                )
            ],
        ),
        (
            "1. me-e+li  me.e:li :\n2. ku",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of(
                            [
                                Reading.of_name("me"),
                                Joiner.hyphen(),
                                Reading.of_name("e"),
                                Joiner.plus(),
                                Reading.of_name("li"),
                            ],
                        ),
                        Word.of(
                            [
                                Reading.of_name("me"),
                                Joiner.dot(),
                                Reading.of_name("e"),
                                Joiner.colon(),
                                Reading.of_name("li"),
                            ],
                        ),
                        Divider.of(":"),
                    ),
                ),
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("2."), (Word.of([Reading.of_name("ku")]),)
                ),
            ],
        ),
        (
            "1. |GAL|",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (Word.of([CompoundGrapheme.of("|GAL|")]),),
                )
            ],
        ),
        (
            "1. !qt !bs !cm !zz",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
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
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of([UnclearSign.of()]),
                        Word.of([UnidentifiedSign.of()]),
                        Word.of(
                            [UnclearSign.of([atf.Flag.UNCERTAIN, atf.Flag.DAMAGE])],
                        ),
                        Word.of(
                            [
                                UnidentifiedSign.of(
                                    [atf.Flag.DAMAGE, atf.Flag.CORRECTION]
                                )
                            ],
                        ),
                    ),
                )
            ],
        ),
        (
            "1. x-ti ti-X",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of(
                            [UnclearSign.of(), Joiner.hyphen(), Reading.of_name("ti"),],
                        ),
                        Word.of(
                            [
                                Reading.of_name("ti"),
                                Joiner.hyphen(),
                                UnidentifiedSign.of(),
                            ],
                        ),
                    ),
                )
            ],
        ),
        (
            "1. [... r]u?-u₂-qu na-a[n-...]\n2. ši-[ku-...-ku]-nu\n3. [...]-ku",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        BrokenAway.open(),
                        UnknownNumberOfSigns(frozenset()),
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
                            ],
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
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                            ],
                        ),
                    ),
                ),
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("2."),
                    (
                        Word.of(
                            parts=[
                                Reading.of_name("ši"),
                                Joiner.hyphen(),
                                BrokenAway.open(),
                                Reading.of_name("ku"),
                                Joiner.hyphen(),
                                UnknownNumberOfSigns(frozenset()),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                Reading.of_name("nu"),
                            ],
                        ),
                    ),
                ),
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("3."),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                            ],
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. [...]-qa-[...]-ba-[...]\n2. pa-[...]",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                Reading.of_name("qa"),
                                Joiner.hyphen(),
                                BrokenAway.open(),
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                Reading.of_name("ba"),
                                Joiner.hyphen(),
                                BrokenAway.open(),
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                            ],
                        ),
                    ),
                ),
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("2."),
                    (
                        Word.of(
                            parts=[
                                Reading.of_name("pa"),
                                Joiner.hyphen(),
                                BrokenAway.open(),
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                            ],
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. [a?-ku (...)]\n2. [a?-ku (x)]",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                Reading.of_name("a", flags=[atf.Flag.UNCERTAIN]),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                            ],
                        ),
                        PerhapsBrokenAway.open(),
                        UnknownNumberOfSigns(frozenset()),
                        PerhapsBrokenAway.close(),
                        BrokenAway.close(),
                    ),
                ),
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("2."),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                Reading.of_name("a", flags=[atf.Flag.UNCERTAIN]),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                            ],
                        ),
                        Word.of(
                            parts=[
                                PerhapsBrokenAway.open(),
                                UnclearSign.of(),
                                PerhapsBrokenAway.close(),
                                BrokenAway.close(),
                            ],
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. [...+ku....] [....ku+...]",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns(frozenset()),
                                Joiner.plus(),
                                Reading.of_name("ku"),
                                Joiner.dot(),
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                            ],
                        ),
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns(frozenset()),
                                Joiner.dot(),
                                Reading.of_name("ku"),
                                Joiner.plus(),
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                            ],
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
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        BrokenAway.open(),
                        UnknownNumberOfSigns(frozenset()),
                        BrokenAway.close(),
                        LoneDeterminative.of_value(
                            [Determinative.of([Reading.of_name("bu")]),],
                            ErasureState.NONE,
                        ),
                        BrokenAway.open(),
                        UnknownNumberOfSigns(frozenset()),
                        BrokenAway.close(),
                    ),
                ),
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("2."),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                                Determinative.of([Reading.of_name("bu")]),
                            ],
                        ),
                        BrokenAway.open(),
                        UnknownNumberOfSigns(frozenset()),
                        BrokenAway.close(),
                    ),
                ),
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("3."),
                    (
                        BrokenAway.open(),
                        UnknownNumberOfSigns(frozenset()),
                        BrokenAway.close(),
                        Word.of(
                            parts=[
                                Determinative.of([Reading.of_name("bu")]),
                                BrokenAway.open(),
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                            ],
                        ),
                    ),
                ),
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("4."),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                                Determinative.of([Reading.of_name("bu")]),
                                BrokenAway.open(),
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                            ],
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. {bu}-nu {bu-bu}-nu\n2. {bu-bu}",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of(
                            parts=[
                                Determinative.of([Reading.of_name("bu")]),
                                Joiner.hyphen(),
                                Reading.of_name("nu"),
                            ],
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
                            ],
                        ),
                    ),
                ),
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("2."),
                    (
                        LoneDeterminative.of_value(
                            [
                                Determinative.of(
                                    [
                                        Reading.of_name("bu"),
                                        Joiner.hyphen(),
                                        Reading.of_name("bu"),
                                    ]
                                ),
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
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of([Logogram.of_name("KIMIN")]),
                        Word.of(
                            parts=[
                                Determinative.of(
                                    [Reading.of_name("u", 2, flags=[atf.Flag.DAMAGE])]
                                ),
                                BrokenAway.open(),
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                            ],
                        ),
                        LoneDeterminative.of_value(
                            [
                                Determinative.of(
                                    [Reading.of_name("u", 2, flags=[atf.Flag.DAMAGE])]
                                ),
                            ],
                            ErasureState.NONE,
                        ),
                        BrokenAway.open(),
                        UnknownNumberOfSigns(frozenset()),
                        BrokenAway.close(),
                    ),
                )
            ],
        ),
        (
            "1. šu gid₂\n2. [U₄].14.KAM₂ U₄.15.KAM₂",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of([Reading.of_name("šu")]),
                        Word.of([Reading.of_name("gid", 2)]),
                    ),
                ),
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("2."),
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
                            ],
                        ),
                        Word.of(
                            parts=[
                                Logogram.of_name("U", 4),
                                Joiner.dot(),
                                Number.of_name("15"),
                                Joiner.dot(),
                                Logogram.of_name("KAM", 2),
                            ],
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. {(he-pi₂ eš-šu₂)}\n2. {(NU SUR)}",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        DocumentOrientedGloss.open(),
                        Word.of(
                            parts=[
                                Reading.of_name("he"),
                                Joiner.hyphen(),
                                Reading.of_name("pi", 2),
                            ],
                        ),
                        Word.of(
                            parts=[
                                Reading.of_name("eš"),
                                Joiner.hyphen(),
                                Reading.of_name("šu", 2),
                            ],
                        ),
                        DocumentOrientedGloss.close(),
                    ),
                ),
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("2."),
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
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Variant.of(Reading.of_name("sal"), Divider.of(":"),),
                        Word.of([Reading.of_name("šim")]),
                    ),
                )
            ],
        ),
        (
            "1. °me-e-li\\ku°",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
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
                ),
            ],
        ),
        (
            "1. me-e-li-°\\ku°",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
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
                                Reading.of_name("ku"),
                                Erasure.close(),
                            ],
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. °me-e-li\\°-ku",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of(
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
                ),
            ],
        ),
        (
            "1. me-°e\\li°-ku",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of(
                            parts=[
                                Reading.of_name("me"),
                                Joiner.hyphen(),
                                Erasure.open(),
                                Reading.of_name("e"),
                                Erasure.center(),
                                Reading.of_name("li"),
                                Erasure.close(),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                            ],
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. me-°e\\li°-me-°e\\li°-ku",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of(
                            parts=[
                                Reading.of_name("me"),
                                Joiner.hyphen(),
                                Erasure.open(),
                                Reading.of_name("e"),
                                Erasure.center(),
                                Reading.of_name("li"),
                                Erasure.close(),
                                Joiner.hyphen(),
                                Reading.of_name("me"),
                                Joiner.hyphen(),
                                Erasure.open(),
                                Reading.of_name("e"),
                                Erasure.center(),
                                Reading.of_name("li"),
                                Erasure.close(),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                            ],
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. sal →",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (Word.of([Reading.of_name("sal")]), LineContinuation.of("→"),),
                )
            ],
        ),
        (
            "2. sal →  ",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("2."),
                    (Word.of([Reading.of_name("sal")]), LineContinuation.of("→"),),
                )
            ],
        ),
        (
            "1. [{(he-pi₂ e]š-šu₂)}",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        BrokenAway.open(),
                        DocumentOrientedGloss.open(),
                        Word.of(
                            parts=[
                                Reading.of_name("he"),
                                Joiner.hyphen(),
                                Reading.of_name("pi", 2),
                            ],
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
                            ],
                        ),
                        DocumentOrientedGloss.close(),
                    ),
                )
            ],
        ),
        (
            "1. [{iti}...]",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                Determinative.of([Reading.of_name("iti")]),
                                UnknownNumberOfSigns(frozenset()),
                                BrokenAway.close(),
                            ],
                        ),
                    ),
                )
            ],
        ),
        (
            "2. RA{k[i}]",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("2."),
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
                                        ),
                                    ]
                                ),
                                BrokenAway.close(),
                            ],
                        ),
                    ),
                )
            ],
        ),
        (
            "2. [in]-<(...)>",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("2."),
                    (
                        Word.of(
                            parts=[
                                BrokenAway.open(),
                                Reading.of_name("in"),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                IntentionalOmission.open(),
                                UnknownNumberOfSigns(frozenset()),
                                IntentionalOmission.close(),
                            ],
                        ),
                    ),
                )
            ],
        ),
        (
            "2. ...{d}kur ... {d}kur",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("2."),
                    (
                        Word.of(
                            parts=[
                                UnknownNumberOfSigns(frozenset()),
                                Determinative.of([Reading.of_name("d")]),
                                Reading.of_name("kur"),
                            ],
                        ),
                        UnknownNumberOfSigns(frozenset()),
                        Word.of(
                            parts=[
                                Determinative.of([Reading.of_name("d")]),
                                Reading.of_name("kur"),
                            ],
                        ),
                    ),
                )
            ],
        ),
        (
            "2. kur{d}... kur{d} ...",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("2."),
                    (
                        Word.of(
                            parts=[
                                Reading.of_name("kur"),
                                Determinative.of([Reading.of_name("d")]),
                                UnknownNumberOfSigns(frozenset()),
                            ],
                        ),
                        Word.of(
                            parts=[
                                Reading.of_name("kur"),
                                Determinative.of([Reading.of_name("d")]),
                            ],
                        ),
                        UnknownNumberOfSigns(frozenset()),
                    ),
                )
            ],
        ),
        (
            "1. mu-un;-e₃ ;",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        Word.of(
                            parts=[
                                Reading.of_name("mu"),
                                Joiner.hyphen(),
                                Reading.of_name("un"),
                                InWordNewline(frozenset()),
                                Joiner.hyphen(),
                                Reading.of_name("e", 3),
                            ],
                        ),
                        Divider.of(";"),
                    ),
                )
            ],
        ),
        (
            "1. [... {(he-p]i₂)}",
            [
                TextLine.of_legacy_iterable(
                    LineNumberLabel.from_atf("1."),
                    (
                        BrokenAway.open(),
                        UnknownNumberOfSigns(frozenset()),
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
                            ],
                        ),
                        DocumentOrientedGloss.close(),
                    ),
                )
            ],
        ),
    ],
)
def test_parse_atf(line: str, expected_tokens: List[Line]):
    assert parse_atf_lark(line).lines == Text.of_iterable(expected_tokens).lines


def test_parse_dividers():
    line, expected_tokens = (
        r'1. :? :#! :# ::? :.@v /@19* :"@20@c |@v@19!',
        [
            TextLine.of_legacy_iterable(
                LineNumberLabel.from_atf("1."),
                (
                    Divider.of(":", tuple(), (atf.Flag.UNCERTAIN,)),
                    Divider.of(":", tuple(), (atf.Flag.DAMAGE, atf.Flag.CORRECTION)),
                    Divider.of(":", tuple(), (atf.Flag.DAMAGE,)),
                    Divider.of("::", tuple(), (atf.Flag.UNCERTAIN,)),
                    Divider.of(":.", ("@v",), tuple()),
                    Divider.of("/", ("@19",), (atf.Flag.COLLATION,)),
                    Divider.of(':"', ("@20", "@c"), tuple()),
                    Divider.of("|", ("@v", "@19"), (atf.Flag.CORRECTION,)),
                ),
            )
        ],
    )
    assert parse_atf_lark(line).lines == Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize("parser", [parse_atf_lark])
def test_parse_atf_invalid(parser):
    with pytest.raises(Exception):
        parser("invalid")


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
        ("%foo", DEFAULT_LANGUAGE),
    ],
)
def test_parse_atf_language_shifts(code: str, expected_language: Language):
    word = "ha-am"
    parts = [Reading.of_name("ha"), Joiner.hyphen(), Reading.of_name("am")]
    line = f"1. {word} {code} {word} %sb {word}"

    expected = Text(
        (
            TextLine.of_legacy_iterable(
                LineNumberLabel.from_atf("1."),
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


def assert_exception_has_errors(exc_info, line_numbers, description):
    assert_that(
        exc_info.value.errors,
        contains_exactly(
            *[
                has_entries({"description": description, "lineNumber": line_number,})
                for line_number in line_numbers
            ]
        ),
    )


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "atf,line_numbers",
    [
        ("1. x\nthis is not valid", [2]),
        ("1'. ($____$) x [...]\n$ (too many underscores)", [1]),
        ("1. me°-e\\li°-ku", [1]),
        ("1. me-°e\\li-°ku", [1]),
        ("1'. → x\n$ (line continuation in the middle)", [1]),
        ("this is not valid\nthis is not valid", [1, 2]),
        ("$ ", [1]),
        ("1. {[me}]\n2. [{me]}\n3. {[me]}", [1, 2, 3]),
    ],
)
def test_invalid_atf(parser, atf, line_numbers):
    with pytest.raises(TransliterationError) as exc_info:
        parser(atf)

    assert_exception_has_errors(exc_info, line_numbers, starts_with("Invalid line"))


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "atf,line_numbers", [("1. x\n2. [", [2]), ("1. [\n2. ]", [1, 2]),],
)
def test_invalid_brackets(parser, atf, line_numbers):
    with pytest.raises(TransliterationError) as exc_info:
        parser(atf)

    assert_exception_has_errors(exc_info, line_numbers, "Invalid brackets.")
