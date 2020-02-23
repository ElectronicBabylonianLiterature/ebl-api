import pytest
from hamcrest import assert_that, contains_exactly, has_entries, starts_with

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import AtLine
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
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    TextLine,
)
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


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        ("", []),
        ("\n", []),
        (
            "#first\n\n#second",
            [
                ControlLine.of_single("#", ValueToken("first")),
                EmptyLine(),
                ControlLine.of_single("#", ValueToken("second")),
            ],
        ),
        (
            "#first\n \n#second",
            [
                ControlLine.of_single("#", ValueToken("first")),
                EmptyLine(),
                ControlLine.of_single("#", ValueToken("second")),
            ],
        ),
        ("&K11111", [ControlLine.of_single("&", ValueToken("K11111"))]),
        ("@reverse", [AtLine(atf.Surface.REVERSE, None, "")]),
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
        ("#some notes", [ControlLine.of_single("#", ValueToken("some notes"))],),
        (
            "=: continuation",
            [ControlLine.of_single("=:", ValueToken(" continuation"))],
        ),
        (
            "a+1.a+2. šu",
            [TextLine("a+1.a+2.", (Word("šu", parts=[Reading.of_name("šu")]),))],
        ),
        ("1. ($___$)", [TextLine("1.", (Tabulation("($___$)"),))]),
        (
            "1. ... [...] (...) [(...)]",
            [
                TextLine(
                    "1.",
                    (
                        UnknownNumberOfSigns(),
                        BrokenAway.open(),
                        UnknownNumberOfSigns(),
                        BrokenAway.close(),
                        PerhapsBrokenAway.open(),
                        UnknownNumberOfSigns(),
                        PerhapsBrokenAway.close(),
                        BrokenAway.open(),
                        PerhapsBrokenAway.open(),
                        UnknownNumberOfSigns(),
                        PerhapsBrokenAway.close(),
                        BrokenAway.close(),
                    ),
                )
            ],
        ),
        (
            "1. [(x x x)]",
            [
                TextLine(
                    "1.",
                    (
                        Word(
                            "[(x",
                            parts=[
                                BrokenAway.open(),
                                PerhapsBrokenAway.open(),
                                UnclearSign(),
                            ],
                        ),
                        Word("x", parts=[UnclearSign()]),
                        Word(
                            "x)]",
                            parts=[
                                UnclearSign(),
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
                TextLine(
                    "1.",
                    (
                        Word(
                            "<en-da-ab-su₈",
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
                        UnknownNumberOfSigns(),
                        AccidentalOmission.close(),
                    ),
                )
            ],
        ),
        (
            "1. <<en ...>>",
            [
                TextLine(
                    "1.",
                    (
                        Word("<<en", parts=[Removal.open(), Reading.of_name("en"),],),
                        UnknownNumberOfSigns(),
                        Removal.close(),
                    ),
                )
            ],
        ),
        ("1. & &12", [TextLine("1.", (Column(), Column(12)))]),
        (
            "1. | : :' :\" :. :: ; /",
            [
                TextLine(
                    "1.",
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
                TextLine(
                    "1.",
                    (
                        Variant.of(Divider.of("|"), Divider.of(":")),
                        Variant.of(
                            Divider.of(":'"),
                            Word("sal", parts=[Reading.of_name("sal")]),
                        ),
                        Variant.of(Divider.of("/"), Divider.of(":")),
                        Variant.of(Divider.of(":"), Divider.of("/")),
                    ),
                )
            ],
        ),
        (
            "1. me-e+li  me.e:li :\n2. ku",
            [
                TextLine(
                    "1.",
                    (
                        Word(
                            "me-e+li",
                            parts=[
                                Reading.of_name("me"),
                                Joiner.hyphen(),
                                Reading.of_name("e"),
                                Joiner.plus(),
                                Reading.of_name("li"),
                            ],
                        ),
                        Word(
                            "me.e:li",
                            parts=[
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
                TextLine("2.", (Word("ku", parts=[Reading.of_name("ku")]),)),
            ],
        ),
        (
            "1. |GAL|",
            [TextLine("1.", (Word("|GAL|", parts=[CompoundGrapheme("|GAL|")]),))],
        ),
        (
            "1. !qt !bs !cm !zz",
            [
                TextLine(
                    "1.",
                    (
                        CommentaryProtocol("!qt"),
                        CommentaryProtocol("!bs"),
                        CommentaryProtocol("!cm"),
                        CommentaryProtocol("!zz"),
                    ),
                )
            ],
        ),
        (
            "1. x X x?# X#!",
            [
                TextLine(
                    "1.",
                    (
                        Word("x", parts=[UnclearSign()]),
                        Word("X", parts=[UnidentifiedSign()]),
                        Word(
                            "x?#",
                            parts=[UnclearSign([atf.Flag.UNCERTAIN, atf.Flag.DAMAGE])],
                        ),
                        Word(
                            "X#!",
                            parts=[
                                UnidentifiedSign([atf.Flag.DAMAGE, atf.Flag.CORRECTION])
                            ],
                        ),
                    ),
                )
            ],
        ),
        (
            "1. x-ti ti-X",
            [
                TextLine(
                    "1.",
                    (
                        Word(
                            "x-ti",
                            parts=[
                                UnclearSign(),
                                Joiner.hyphen(),
                                Reading.of_name("ti"),
                            ],
                        ),
                        Word(
                            "ti-X",
                            parts=[
                                Reading.of_name("ti"),
                                Joiner.hyphen(),
                                UnidentifiedSign(),
                            ],
                        ),
                    ),
                )
            ],
        ),
        (
            "1. [... r]u?-u₂-qu na-a[n-...]\n2. ši-[ku-...-ku]-nu\n3. [...]-ku",
            [
                TextLine(
                    "1.",
                    (
                        BrokenAway.open(),
                        UnknownNumberOfSigns(),
                        Word(
                            "r]u?-u₂-qu",
                            parts=[
                                Reading.of(
                                    (
                                        ValueToken("r"),
                                        BrokenAway.close(),
                                        ValueToken("u"),
                                    ),
                                    flags=[atf.Flag.UNCERTAIN],
                                ),
                                Joiner.hyphen(),
                                Reading.of_name("u", 2),
                                Joiner.hyphen(),
                                Reading.of_name("qu"),
                            ],
                        ),
                        Word(
                            "na-a[n-...]",
                            parts=[
                                Reading.of_name("na"),
                                Joiner.hyphen(),
                                Reading.of(
                                    (
                                        ValueToken("a"),
                                        BrokenAway.open(),
                                        ValueToken("n"),
                                    )
                                ),
                                Joiner.hyphen(),
                                UnknownNumberOfSigns(),
                                BrokenAway.close(),
                            ],
                        ),
                    ),
                ),
                TextLine(
                    "2.",
                    (
                        Word(
                            "ši-[ku-...-ku]-nu",
                            parts=[
                                Reading.of_name("ši"),
                                Joiner.hyphen(),
                                BrokenAway.open(),
                                Reading.of_name("ku"),
                                Joiner.hyphen(),
                                UnknownNumberOfSigns(),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                Reading.of_name("nu"),
                            ],
                        ),
                    ),
                ),
                TextLine(
                    "3.",
                    (
                        Word(
                            "[...]-ku",
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns(),
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
            "1. ša₃] [{d}UTU [ :",
            [
                TextLine(
                    "1.",
                    (
                        Word(
                            "ša₃]",
                            parts=[Reading.of_name("ša", 3), BrokenAway.close()],
                        ),
                        Word(
                            "[{d}UTU",
                            parts=[
                                BrokenAway.open(),
                                Determinative([Reading.of_name("d")]),
                                Logogram.of_name("UTU"),
                            ],
                        ),
                        BrokenAway.open(),
                        Divider.of(":"),
                    ),
                )
            ],
        ),
        (
            "1. [...]-qa-[...]-ba-[...]\n2. pa-[...]",
            [
                TextLine(
                    "1.",
                    (
                        Word(
                            "[...]-qa-[...]-ba-[...]",
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns(),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                Reading.of_name("qa"),
                                Joiner.hyphen(),
                                BrokenAway.open(),
                                UnknownNumberOfSigns(),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                Reading.of_name("ba"),
                                Joiner.hyphen(),
                                BrokenAway.open(),
                                UnknownNumberOfSigns(),
                                BrokenAway.close(),
                            ],
                        ),
                    ),
                ),
                TextLine(
                    "2.",
                    (
                        Word(
                            "pa-[...]",
                            parts=[
                                Reading.of_name("pa"),
                                Joiner.hyphen(),
                                BrokenAway.open(),
                                UnknownNumberOfSigns(),
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
                TextLine(
                    "1.",
                    (
                        Word(
                            "[a?-ku",
                            parts=[
                                BrokenAway.open(),
                                Reading.of_name("a", flags=[atf.Flag.UNCERTAIN]),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                            ],
                        ),
                        PerhapsBrokenAway.open(),
                        UnknownNumberOfSigns(),
                        PerhapsBrokenAway.close(),
                        BrokenAway.close(),
                    ),
                ),
                TextLine(
                    "2.",
                    (
                        Word(
                            "[a?-ku",
                            parts=[
                                BrokenAway.open(),
                                Reading.of_name("a", flags=[atf.Flag.UNCERTAIN]),
                                Joiner.hyphen(),
                                Reading.of_name("ku"),
                            ],
                        ),
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
                ),
            ],
        ),
        (
            "1. [...+ku....] [....ku+...]",
            [
                TextLine(
                    "1.",
                    (
                        Word(
                            "[...+ku....]",
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns(),
                                Joiner.plus(),
                                Reading.of_name("ku"),
                                Joiner.dot(),
                                UnknownNumberOfSigns(),
                                BrokenAway.close(),
                            ],
                        ),
                        Word(
                            "[....ku+...]",
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns(),
                                Joiner.dot(),
                                Reading.of_name("ku"),
                                Joiner.plus(),
                                UnknownNumberOfSigns(),
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
                TextLine(
                    "1.",
                    (
                        BrokenAway.open(),
                        UnknownNumberOfSigns(),
                        BrokenAway.close(),
                        LoneDeterminative.of_value(
                            "{bu}",
                            ErasureState.NONE,
                            [Determinative([Reading.of_name("bu")]),],
                        ),
                        BrokenAway.open(),
                        UnknownNumberOfSigns(),
                        BrokenAway.close(),
                    ),
                ),
                TextLine(
                    "2.",
                    (
                        Word(
                            "[...]{bu}",
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns(),
                                BrokenAway.close(),
                                Determinative([Reading.of_name("bu")]),
                            ],
                        ),
                        BrokenAway.open(),
                        UnknownNumberOfSigns(),
                        BrokenAway.close(),
                    ),
                ),
                TextLine(
                    "3.",
                    (
                        BrokenAway.open(),
                        UnknownNumberOfSigns(),
                        BrokenAway.close(),
                        Word(
                            "{bu}[...]",
                            parts=[
                                Determinative([Reading.of_name("bu")]),
                                BrokenAway.open(),
                                UnknownNumberOfSigns(),
                                BrokenAway.close(),
                            ],
                        ),
                    ),
                ),
                TextLine(
                    "4.",
                    (
                        Word(
                            "[...]{bu}[...]",
                            parts=[
                                BrokenAway.open(),
                                UnknownNumberOfSigns(),
                                BrokenAway.close(),
                                Determinative([Reading.of_name("bu")]),
                                BrokenAway.open(),
                                UnknownNumberOfSigns(),
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
                TextLine(
                    "1.",
                    (
                        Word(
                            "{bu}-nu",
                            parts=[
                                Determinative([Reading.of_name("bu")]),
                                Joiner.hyphen(),
                                Reading.of_name("nu"),
                            ],
                        ),
                        Word(
                            "{bu-bu}-nu",
                            parts=[
                                Determinative(
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
                TextLine(
                    "2.",
                    (
                        LoneDeterminative.of_value(
                            "{bu-bu}",
                            ErasureState.NONE,
                            [
                                Determinative(
                                    [
                                        Reading.of_name("bu"),
                                        Joiner.hyphen(),
                                        Reading.of_name("bu"),
                                    ]
                                ),
                            ],
                        ),
                    ),
                ),
            ],
        ),
        (
            "1. KIMIN {u₂#}[...] {u₂#} [...]",
            [
                TextLine(
                    "1.",
                    (
                        Word("KIMIN", parts=[Logogram.of_name("KIMIN")]),
                        Word(
                            "{u₂#}[...]",
                            parts=[
                                Determinative(
                                    [Reading.of_name("u", 2, flags=[atf.Flag.DAMAGE])]
                                ),
                                BrokenAway.open(),
                                UnknownNumberOfSigns(),
                                BrokenAway.close(),
                            ],
                        ),
                        LoneDeterminative.of_value(
                            "{u₂#}",
                            ErasureState.NONE,
                            [
                                Determinative(
                                    [Reading.of_name("u", 2, flags=[atf.Flag.DAMAGE])]
                                ),
                            ],
                        ),
                        BrokenAway.open(),
                        UnknownNumberOfSigns(),
                        BrokenAway.close(),
                    ),
                )
            ],
        ),
        (
            "1. šu gid₂\n2. U₄].14.KAM₂ U₄.15.KAM₂",
            [
                TextLine(
                    "1.",
                    (
                        Word("šu", parts=[Reading.of_name("šu")]),
                        Word("gid₂", parts=[Reading.of_name("gid", 2)]),
                    ),
                ),
                TextLine(
                    "2.",
                    (
                        Word(
                            "U₄].14.KAM₂",
                            parts=[
                                Logogram.of_name("U", 4),
                                BrokenAway.close(),
                                Joiner.dot(),
                                Number.of_name("14"),
                                Joiner.dot(),
                                Logogram.of_name("KAM", 2),
                            ],
                        ),
                        Word(
                            "U₄.15.KAM₂",
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
                TextLine(
                    "1.",
                    (
                        DocumentOrientedGloss.open(),
                        Word(
                            "he-pi₂",
                            parts=[
                                Reading.of_name("he"),
                                Joiner.hyphen(),
                                Reading.of_name("pi", 2),
                            ],
                        ),
                        Word(
                            "eš-šu₂",
                            parts=[
                                Reading.of_name("eš"),
                                Joiner.hyphen(),
                                Reading.of_name("šu", 2),
                            ],
                        ),
                        DocumentOrientedGloss.close(),
                    ),
                ),
                TextLine(
                    "2.",
                    (
                        DocumentOrientedGloss.open(),
                        Word("NU", parts=[Logogram.of_name("NU")]),
                        Word("SUR", parts=[Logogram.of_name("SUR")]),
                        DocumentOrientedGloss.close(),
                    ),
                ),
            ],
        ),
        (
            "1.  sal/: šim ",
            [
                TextLine(
                    "1.",
                    (
                        Variant.of(
                            Word("sal", parts=[Reading.of_name("sal")]),
                            Divider.of(":"),
                        ),
                        Word("šim", parts=[Reading.of_name("šim")]),
                    ),
                )
            ],
        ),
        (
            "1. °me-e-li\\ku°",
            [
                TextLine(
                    "1.",
                    (
                        Erasure.open(),
                        Word(
                            "me-e-li",
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
                        Word(
                            "ku",
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
                TextLine(
                    "1.",
                    (
                        Word(
                            "me-e-li-°\\ku°",
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
                TextLine(
                    "1.",
                    (
                        Word(
                            "°me-e-li\\°-ku",
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
                TextLine(
                    "1.",
                    (
                        Word(
                            "me-°e\\li°-ku",
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
                TextLine(
                    "1.",
                    (
                        Word(
                            "me-°e\\li°-me-°e\\li°-ku",
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
                TextLine(
                    "1.",
                    (
                        Word("sal", parts=[Reading.of_name("sal")]),
                        LineContinuation("→"),
                    ),
                )
            ],
        ),
        (
            "2. sal →  ",
            [
                TextLine(
                    "2.",
                    (
                        Word("sal", parts=[Reading.of_name("sal")]),
                        LineContinuation("→"),
                    ),
                )
            ],
        ),
        (
            "1. [{(he-pi₂ e]š-šu₂)}",
            [
                TextLine(
                    "1.",
                    (
                        BrokenAway.open(),
                        DocumentOrientedGloss.open(),
                        Word(
                            "he-pi₂",
                            parts=[
                                Reading.of_name("he"),
                                Joiner.hyphen(),
                                Reading.of_name("pi", 2),
                            ],
                        ),
                        Word(
                            "e]š-šu₂",
                            parts=[
                                Reading.of(
                                    (
                                        ValueToken("e"),
                                        BrokenAway.close(),
                                        ValueToken("š"),
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
                TextLine(
                    "1.",
                    (
                        Word(
                            "[{iti}...]",
                            parts=[
                                BrokenAway.open(),
                                Determinative([Reading.of_name("iti")]),
                                UnknownNumberOfSigns(),
                                BrokenAway.close(),
                            ],
                        ),
                    ),
                )
            ],
        ),
        (
            "2. RA{k[i]}",
            [
                TextLine(
                    "2.",
                    (
                        Word(
                            "RA{k[i]}",
                            parts=[
                                Logogram.of_name("RA"),
                                Determinative(
                                    [
                                        Reading.of(
                                            (
                                                ValueToken("k"),
                                                BrokenAway.open(),
                                                ValueToken("i"),
                                            )
                                        ),
                                        BrokenAway.close(),
                                    ]
                                ),
                            ],
                        ),
                    ),
                )
            ],
        ),
        (
            "2. in]-<(...)>",
            [
                TextLine(
                    "2.",
                    (
                        Word(
                            "in]-<(...)>",
                            parts=[
                                Reading.of_name("in"),
                                BrokenAway.close(),
                                Joiner.hyphen(),
                                IntentionalOmission.open(),
                                UnknownNumberOfSigns(),
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
                TextLine(
                    "2.",
                    (
                        Word(
                            "...{d}kur",
                            parts=[
                                UnknownNumberOfSigns(),
                                Determinative([Reading.of_name("d")]),
                                Reading.of_name("kur"),
                            ],
                        ),
                        UnknownNumberOfSigns(),
                        Word(
                            "{d}kur",
                            parts=[
                                Determinative([Reading.of_name("d")]),
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
                TextLine(
                    "2.",
                    (
                        Word(
                            "kur{d}...",
                            parts=[
                                Reading.of_name("kur"),
                                Determinative([Reading.of_name("d")]),
                                UnknownNumberOfSigns(),
                            ],
                        ),
                        Word(
                            "kur{d}",
                            parts=[
                                Reading.of_name("kur"),
                                Determinative([Reading.of_name("d")]),
                            ],
                        ),
                        UnknownNumberOfSigns(),
                    ),
                )
            ],
        ),
        (
            "1. mu-un;-e₃ ;",
            [
                TextLine(
                    "1.",
                    (
                        Word(
                            "mu-un;-e₃",
                            parts=[
                                Reading.of_name("mu"),
                                Joiner.hyphen(),
                                Reading.of_name("un"),
                                InWordNewline(),
                                Joiner.hyphen(),
                                Reading.of_name("e", 3),
                            ],
                        ),
                        Divider.of(";"),
                    ),
                )
            ],
        ),
    ],
)
def test_parse_atf(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines


def test_parse_dividers():
    line, expected_tokens = (
        r'1. :? :#! :# ::? :.@v /@19* :"@20@c |@v@19!',
        [
            TextLine(
                "1.",
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


@pytest.mark.parametrize("parser", [parse_atf_lark])
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
def test_parse_atf_language_shifts(parser, code, expected_language):
    word = "ha-am"
    parts = [Reading.of_name("ha"), Joiner(atf.Joiner.HYPHEN), Reading.of_name("am")]
    line = f"1. {word} {code} {word} %sb {word}"

    expected = Text(
        (
            TextLine(
                "1.",
                (
                    Word(word, DEFAULT_LANGUAGE, parts=parts),
                    LanguageShift(code),
                    Word(word, expected_language, parts=parts),
                    LanguageShift("%sb"),
                    Word(word, Language.AKKADIAN, parts=parts),
                ),
            ),
        )
    )

    assert parser(line).lines == expected.lines


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
    ],
)
def test_invalid_atf(parser, atf, line_numbers):
    with pytest.raises(TransliterationError) as exc_info:
        parser(atf)

    assert_that(
        exc_info.value.errors,
        contains_exactly(
            *[
                has_entries(
                    {
                        "description": starts_with("Invalid line"),
                        "lineNumber": line_number,
                    }
                )
                for line_number in line_numbers
            ]
        ),
    )
