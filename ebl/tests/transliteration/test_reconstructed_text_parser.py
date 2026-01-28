import re

import pytest
from lark.exceptions import ParseError, UnexpectedInput

from ebl.corpus.domain.enclosure_validator import validate
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Emendation,
    PerhapsBrokenAway,
)
from ebl.transliteration.domain.normalized_akkadian import (
    AkkadianWord,
    Caesura,
    MetricalFootSeparator,
)
from ebl.transliteration.domain.atf_parsers.reconstructed_text_parser import (
    parse_break,
    parse_reconstructed_line,
    parse_reconstructed_word,
)
from ebl.transliteration.domain.tokens import (
    Joiner,
    LanguageShift,
    UnknownNumberOfSigns,
    ValueToken,
)


def assert_parse(parser, expected, text):
    assert [token for token in parser(text) if token] == expected


def assert_parse_error(parser, text):
    with pytest.raises((UnexpectedInput, ParseError)):
        parser(text)


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            "ʾABDEGHIKLMNPSTUYZabcdefghiklmnpqrstuwyzÉâêîûāĒēīŠšūṣṭ₄",
            [
                ValueToken.of(
                    "ʾABDEGHIKLMNPSTUYZabcdefghiklmnpqrstuwyzÉâêîûāĒēīŠšūṣṭ₄"
                ),
                [],
            ],
        ),
        ("ibnû?", [ValueToken.of("ibnû"), [Flag.UNCERTAIN]]),
        ("ibnû#", [ValueToken.of("ibnû"), [Flag.DAMAGE]]),
        ("ibnû!", [ValueToken.of("ibnû"), [Flag.CORRECTION]]),
        ("ibnû#?", [ValueToken.of("ibnû"), [Flag.DAMAGE, Flag.UNCERTAIN]]),
        ("ibnû?#", [ValueToken.of("ibnû"), [Flag.UNCERTAIN, Flag.DAMAGE]]),
        (
            "ibnû?#!",
            [ValueToken.of("ibnû"), [Flag.UNCERTAIN, Flag.DAMAGE, Flag.CORRECTION]],
        ),
        ("ibnû##", [ValueToken.of("ibnû"), [Flag.DAMAGE]]),
        ("[ibnû]", [BrokenAway.open(), ValueToken.of("ibnû"), BrokenAway.close(), []]),
        ("ib[nû", [ValueToken.of("ib"), BrokenAway.open(), ValueToken.of("nû"), []]),
        ("ib]nû", [ValueToken.of("ib"), BrokenAway.close(), ValueToken.of("nû"), []]),
        (
            "i[b]nû",
            [
                ValueToken.of("i"),
                BrokenAway.open(),
                ValueToken.of("b"),
                BrokenAway.close(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        ("ibnû?]", [ValueToken.of("ibnû"), BrokenAway.close(), [Flag.UNCERTAIN]]),
        (
            "(ibnû)",
            [
                PerhapsBrokenAway.open(),
                ValueToken.of("ibnû"),
                PerhapsBrokenAway.close(),
                [],
            ],
        ),
        (
            "ib(nû",
            [ValueToken.of("ib"), PerhapsBrokenAway.open(), ValueToken.of("nû"), []],
        ),
        (
            "ib)nû",
            [ValueToken.of("ib"), PerhapsBrokenAway.close(), ValueToken.of("nû"), []],
        ),
        (
            "i(b)nû",
            [
                ValueToken.of("i"),
                PerhapsBrokenAway.open(),
                ValueToken.of("b"),
                PerhapsBrokenAway.close(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        ("ibnû#)", [ValueToken.of("ibnû"), PerhapsBrokenAway.close(), [Flag.DAMAGE]]),
        (
            "[(ibnû)]",
            [
                BrokenAway.open(),
                PerhapsBrokenAway.open(),
                ValueToken.of("ibnû"),
                PerhapsBrokenAway.close(),
                BrokenAway.close(),
                [],
            ],
        ),
        (
            "ib[(nû",
            [
                ValueToken.of("ib"),
                BrokenAway.open(),
                PerhapsBrokenAway.open(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        (
            "ib)]nû",
            [
                ValueToken.of("ib"),
                PerhapsBrokenAway.close(),
                BrokenAway.close(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        (
            "i[(b)]nû",
            [
                ValueToken.of("i"),
                BrokenAway.open(),
                PerhapsBrokenAway.open(),
                ValueToken.of("b"),
                PerhapsBrokenAway.close(),
                BrokenAway.close(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        (
            "[i(b)n]û",
            [
                BrokenAway.open(),
                ValueToken.of("i"),
                PerhapsBrokenAway.open(),
                ValueToken.of("b"),
                PerhapsBrokenAway.close(),
                ValueToken.of("n"),
                BrokenAway.close(),
                ValueToken.of("û"),
                [],
            ],
        ),
        (
            "ibnû?)]",
            [
                ValueToken.of("ibnû"),
                PerhapsBrokenAway.close(),
                BrokenAway.close(),
                [Flag.UNCERTAIN],
            ],
        ),
        ("<ibnû>", [Emendation.open(), ValueToken.of("ibnû"), Emendation.close(), []]),
        ("ib<nû", [ValueToken.of("ib"), Emendation.open(), ValueToken.of("nû"), []]),
        ("ib>nû", [ValueToken.of("ib"), Emendation.close(), ValueToken.of("nû"), []]),
        (
            "i<b>nû",
            [
                ValueToken.of("i"),
                Emendation.open(),
                ValueToken.of("b"),
                Emendation.close(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        ("ibnû?>", [ValueToken.of("ibnû"), Emendation.close(), [Flag.UNCERTAIN]]),
        ("...ibnû", [UnknownNumberOfSigns.of(), ValueToken.of("ibnû"), []]),
        ("ibnû...", [ValueToken.of("ibnû"), UnknownNumberOfSigns.of(), []]),
        (
            "ib...nû",
            [ValueToken.of("ib"), UnknownNumberOfSigns.of(), ValueToken.of("nû"), []],
        ),
        (
            "<...ibnû",
            [Emendation.open(), UnknownNumberOfSigns.of(), ValueToken.of("ibnû"), []],
        ),
        (
            "ibnû...>",
            [ValueToken.of("ibnû"), UnknownNumberOfSigns.of(), Emendation.close(), []],
        ),
        (
            "...>ibnû",
            [UnknownNumberOfSigns.of(), Emendation.close(), ValueToken.of("ibnû"), []],
        ),
        (
            "ibnû<...",
            [ValueToken.of("ibnû"), Emendation.open(), UnknownNumberOfSigns.of(), []],
        ),
        (
            "<...>ibnû",
            [
                Emendation.open(),
                UnknownNumberOfSigns.of(),
                Emendation.close(),
                ValueToken.of("ibnû"),
                [],
            ],
        ),
        (
            "ibnû<...>",
            [
                ValueToken.of("ibnû"),
                Emendation.open(),
                UnknownNumberOfSigns.of(),
                Emendation.close(),
                [],
            ],
        ),
        (
            "ib<...nû",
            [
                ValueToken.of("ib"),
                Emendation.open(),
                UnknownNumberOfSigns.of(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        (
            "ib...>nû",
            [
                ValueToken.of("ib"),
                UnknownNumberOfSigns.of(),
                Emendation.close(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        (
            "ib<...>nû",
            [
                ValueToken.of("ib"),
                Emendation.open(),
                UnknownNumberOfSigns.of(),
                Emendation.close(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        (
            "[<(ibnû)]>",
            [
                BrokenAway.open(),
                Emendation.open(),
                PerhapsBrokenAway.open(),
                ValueToken.of("ibnû"),
                PerhapsBrokenAway.close(),
                BrokenAway.close(),
                Emendation.close(),
                [],
            ],
        ),
        (
            "ib<[(nû",
            [
                ValueToken.of("ib"),
                Emendation.open(),
                BrokenAway.open(),
                PerhapsBrokenAway.open(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        (
            "ib)]>nû",
            [
                ValueToken.of("ib"),
                PerhapsBrokenAway.close(),
                BrokenAway.close(),
                Emendation.close(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        (
            "i[<(b)]>nû",
            [
                ValueToken.of("i"),
                BrokenAway.open(),
                Emendation.open(),
                PerhapsBrokenAway.open(),
                ValueToken.of("b"),
                PerhapsBrokenAway.close(),
                BrokenAway.close(),
                Emendation.close(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        (
            "[i(<b>)n]û",
            [
                BrokenAway.open(),
                ValueToken.of("i"),
                PerhapsBrokenAway.open(),
                Emendation.open(),
                ValueToken.of("b"),
                Emendation.close(),
                PerhapsBrokenAway.close(),
                ValueToken.of("n"),
                BrokenAway.close(),
                ValueToken.of("û"),
                [],
            ],
        ),
        (
            "ibnû?)>]",
            [
                ValueToken.of("ibnû"),
                PerhapsBrokenAway.close(),
                Emendation.close(),
                BrokenAway.close(),
                [Flag.UNCERTAIN],
            ],
        ),
        ("ib-nû", [ValueToken.of("ib"), Joiner.hyphen(), ValueToken.of("nû"), []]),
        (
            "...-nû",
            [UnknownNumberOfSigns.of(), Joiner.hyphen(), ValueToken.of("nû"), []],
        ),
        (
            "ib-...",
            [ValueToken.of("ib"), Joiner.hyphen(), UnknownNumberOfSigns.of(), []],
        ),
        (
            "...]-nû",
            [
                UnknownNumberOfSigns.of(),
                BrokenAway.close(),
                Joiner.hyphen(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        (
            "ib-[...",
            [
                ValueToken.of("ib"),
                Joiner.hyphen(),
                BrokenAway.open(),
                UnknownNumberOfSigns.of(),
                [],
            ],
        ),
        (
            "ib[-nû",
            [
                ValueToken.of("ib"),
                BrokenAway.open(),
                Joiner.hyphen(),
                ValueToken.of("nû"),
                [],
            ],
        ),
        (
            "ib-]nû",
            [
                ValueToken.of("ib"),
                Joiner.hyphen(),
                BrokenAway.close(),
                ValueToken.of("nû"),
                [],
            ],
        ),
    ],
)
def test_word(text, expected) -> None:
    assert parse_reconstructed_word(text) == AkkadianWord.of(
        tuple(expected[:-1]), tuple(expected[-1])
    )


@pytest.mark.parametrize(
    "text",
    [
        "x",
        "X",
        "KUR",
        "ibnû*",
        "ibnû?#?!",
        "]ibnû",
        "ibnû[",
        ")ibnû",
        "ibnû(",
        ">ibnû",
        "ibnû<",
        "ibnû?[#",
        "ibnû#)?",
        "ibnû#>?",
        "ibnû]?",
        "ibnû)#",
        "ibnû)]?",
        "ibnû>!",
        "ib.[..nû",
        ".(..ibnû",
        "ibnû.>]..",
        "ib..nû",
        "..ibnû",
        "ibnû..",
        "ib....nû",
        "....ibnû",
        "ibnû....",
        "ib......nû",
        "......ibnû",
        "ibnû......",
        "...",
        "[...]",
        "(...)",
        "[(...)]",
        "ib[-]nû",
        "ib]-[nû",
    ],
)
def test_invalid_word(text) -> None:
    assert_parse_error(parse_reconstructed_word, text)


@pytest.mark.parametrize("text,is_uncertain", [("||", False), ("(||)", True)])
def test_caesura(text, is_uncertain) -> None:
    assert (
        parse_break(text) == Caesura.uncertain() if is_uncertain else Caesura.certain()
    )


@pytest.mark.parametrize("text,is_uncertain", [("|", False), ("(|)", True)])
def test_feet_separator(text, is_uncertain) -> None:
    assert (
        parse_break(text) == MetricalFootSeparator.uncertain()
        if is_uncertain
        else MetricalFootSeparator.certain()
    )


@pytest.mark.parametrize("text", ["|||", "||||", "[|]", "[(|)]", "[||]", "[(||)]"])
def test_invalid_break(text) -> None:
    assert_parse_error(parse_break, text)


WORD = AkkadianWord.of((ValueToken.of("ibnû"),))


@pytest.mark.parametrize(
    "text,expected",
    [
        ("ibnû", (WORD,)),
        ("... ibnû", (UnknownNumberOfSigns.of(), WORD)),
        ("ibnû ...", (WORD, UnknownNumberOfSigns.of())),
        (
            "[...] ibnû",
            (BrokenAway.open(), UnknownNumberOfSigns.of(), BrokenAway.close(), WORD),
        ),
        (
            "ibnû [...]",
            (WORD, BrokenAway.open(), UnknownNumberOfSigns.of(), BrokenAway.close()),
        ),
        (
            "...ibnû",
            (AkkadianWord.of((UnknownNumberOfSigns.of(), ValueToken.of("ibnû"))),),
        ),
        (
            "ibnû...",
            (AkkadianWord.of((ValueToken.of("ibnû"), UnknownNumberOfSigns.of())),),
        ),
        (
            "ib...nû",
            (
                AkkadianWord.of(
                    (
                        ValueToken.of("ib"),
                        UnknownNumberOfSigns.of(),
                        ValueToken.of("nû"),
                    )
                ),
            ),
        ),
        ("ibnû | ibnû", (WORD, MetricalFootSeparator.certain(), WORD)),
        ("ibnû (|) ibnû", (WORD, MetricalFootSeparator.uncertain(), WORD)),
        ("ibnû || ibnû", (WORD, Caesura.certain(), WORD)),
        ("ibnû (||) ibnû", (WORD, Caesura.uncertain(), WORD)),
        ("...", (UnknownNumberOfSigns.of(),)),
        ("[...", (BrokenAway.open(), UnknownNumberOfSigns.of())),
        ("...]", (UnknownNumberOfSigns.of(), BrokenAway.close())),
        ("[...]", (BrokenAway.open(), UnknownNumberOfSigns.of(), BrokenAway.close())),
        ("(...", (PerhapsBrokenAway.open(), UnknownNumberOfSigns.of())),
        ("...)", (UnknownNumberOfSigns.of(), PerhapsBrokenAway.close())),
        (
            "(...)",
            (
                PerhapsBrokenAway.open(),
                UnknownNumberOfSigns.of(),
                PerhapsBrokenAway.close(),
            ),
        ),
        (
            "[(...",
            (BrokenAway.open(), PerhapsBrokenAway.open(), UnknownNumberOfSigns.of()),
        ),
        (
            "...)]",
            (UnknownNumberOfSigns.of(), PerhapsBrokenAway.close(), BrokenAway.close()),
        ),
        (
            "[(...)]",
            (
                BrokenAway.open(),
                PerhapsBrokenAway.open(),
                UnknownNumberOfSigns.of(),
                PerhapsBrokenAway.close(),
                BrokenAway.close(),
            ),
        ),
        ("<...", (Emendation.open(), UnknownNumberOfSigns.of())),
        ("...>", (UnknownNumberOfSigns.of(), Emendation.close())),
        ("<...>", (Emendation.open(), UnknownNumberOfSigns.of(), Emendation.close())),
    ],
)
def test_reconstructed_line(text, expected) -> None:
    assert parse_reconstructed_line(f"%n {text}") == (
        LanguageShift.normalized_akkadian(),
        *expected,
    )


@pytest.mark.parametrize(
    "text",
    [
        "|",
        "(|)",
        "||",
        "(||)",
        "| ||",
        "ibnû (|)",
        "|| ibnû",
        "... (||)",
        "(|) ...",
        "ibnû | | ibnû",
        "ibnû | || ibnû",
        ".",
        "..",
        "....",
        "......",
        "]...",
        "...[",
        ")...",
        "...(",
        ".)..",
        "..].",
        "..[(.",
        "...?",
        "...#",
        "...!",
    ],
)
def test_invalid_reconstructed_line(text) -> None:
    with pytest.raises(  # pyre-ignore[16]
        ValueError, match=f"Invalid reconstructed line: %n {re.escape(text)}"
    ):
        parse_reconstructed_line(f"%n {text}")


@pytest.mark.parametrize(
    "text",
    [
        "[ibnû",
        "(ibnû",
        "[(ibnû",
        "ibnû]",
        "ibnû)",
        "ibnû)]" "[ibnû)]",
        "[(ibnû]" "[... [ibnû] ...]",
        "[(... [ibnû] ...)]",
        "[(... (ibnû) ...)]",
        "[[...",
        "...))",
        "([...",
        "...])",
        "[[ibnû",
        "((ibnû",
        "i([bnû",
        "i])bnû",
        "i[)]bnû",
    ],
)
def test_validate_invalid(text) -> None:
    line = parse_reconstructed_line(f"%n {text}")
    with pytest.raises(ValueError):  # pyre-ignore[16]
        validate(line)


@pytest.mark.parametrize(
    "text",
    [
        "[ma-]ma [ma]-ma [...-]ma",
        "[(ma-)]ma [ma]-ma [(...)]-ma",
        "[(ma-)ma ma]-ma [...(-ma)]",
    ],
)
def test_validate_valid(text) -> None:
    line = parse_reconstructed_line(f"%n {text}")
    validate(line)
