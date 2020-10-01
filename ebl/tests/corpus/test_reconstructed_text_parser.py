import pytest  # pyre-ignore[21]

from ebl.corpus.application.reconstructed_text_parser import (
    parse_break,
    parse_lacuna,
    parse_reconstructed_line,
    parse_reconstructed_word,
)
from ebl.corpus.domain.enclosure_validator import validate
from ebl.corpus.domain.reconstructed_text import (
    AkkadianWord,
    Caesura,
    Lacuna,
    MetricalFootSeparator,
    Modifier,
)
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Emendation,
    PerhapsBrokenAway,
)
from ebl.transliteration.domain.tokens import Joiner, UnknownNumberOfSigns, ValueToken
from lark.exceptions import ParseError, UnexpectedInput  # pyre-ignore[21]
import re


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
        ("ibnû?", [ValueToken.of("ibnû"), [Modifier.UNCERTAIN]]),
        ("ibnû#", [ValueToken.of("ibnû"), [Modifier.DAMAGED]]),
        ("ibnû!", [ValueToken.of("ibnû"), [Modifier.CORRECTED]]),
        ("ibnû#?", [ValueToken.of("ibnû"), [Modifier.DAMAGED, Modifier.UNCERTAIN]]),
        ("ibnû?#", [ValueToken.of("ibnû"), [Modifier.UNCERTAIN, Modifier.DAMAGED]]),
        (
            "ibnû?#!",
            [
                ValueToken.of("ibnû"),
                [Modifier.UNCERTAIN, Modifier.DAMAGED, Modifier.CORRECTED],
            ],
        ),
        ("ibnû##", [ValueToken.of("ibnû"), [Modifier.DAMAGED]]),
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
        ("ibnû?]", [ValueToken.of("ibnû"), BrokenAway.close(), [Modifier.UNCERTAIN]]),
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
        (
            "ibnû#)",
            [ValueToken.of("ibnû"), PerhapsBrokenAway.close(), [Modifier.DAMAGED]],
        ),
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
                [Modifier.UNCERTAIN],
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
        ("ibnû?>", [ValueToken.of("ibnû"), Emendation.close(), [Modifier.UNCERTAIN]]),
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
                [Modifier.UNCERTAIN],
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


@pytest.mark.parametrize(
    "text,before,after",
    [
        ("...", tuple(), tuple()),
        ("[...", (BrokenAway.open(),), tuple()),
        ("...]", tuple(), (BrokenAway.close(),)),
        ("[...]", (BrokenAway.open(),), (BrokenAway.close(),)),
        ("(...", (PerhapsBrokenAway.open(),), tuple()),
        ("...)", tuple(), (PerhapsBrokenAway.close(),)),
        ("(...)", (PerhapsBrokenAway.open(),), (PerhapsBrokenAway.close(),)),
        ("[(...", (BrokenAway.open(), PerhapsBrokenAway.open()), tuple()),
        ("...)]", tuple(), (PerhapsBrokenAway.close(), BrokenAway.close())),
        (
            "[(...)]",
            (BrokenAway.open(), PerhapsBrokenAway.open()),
            (PerhapsBrokenAway.close(), BrokenAway.close()),
        ),
    ],
)
def test_lacuna(text, before, after) -> None:
    assert parse_lacuna(text) == Lacuna.of(before, after)


@pytest.mark.parametrize(
    "text",
    [
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
def test_invalid_lacuna(text) -> None:
    assert_parse_error(parse_lacuna, text)


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
        ("...", (Lacuna.of(tuple(), tuple()),)),
        ("... ibnû", (Lacuna.of(tuple(), tuple()), WORD)),
        ("ibnû ...", (WORD, Lacuna.of(tuple(), tuple()))),
        ("[...] ibnû", (Lacuna.of((BrokenAway.open(),), (BrokenAway.close(),)), WORD)),
        ("ibnû [...]", (WORD, Lacuna.of((BrokenAway.open(),), (BrokenAway.close(),)))),
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
    ],
)
def test_reconstructed_line(text, expected) -> None:
    assert parse_reconstructed_line(text) == expected


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
    ],
)
def test_invalid_reconstructed_line(text) -> None:
    with pytest.raises(
        ValueError, match=f"Invalid reconstructed line: {re.escape(text)}"
    ):
        parse_reconstructed_line(text)


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
    line = parse_reconstructed_line(text)
    with pytest.raises(ValueError):
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
    line = parse_reconstructed_line(text)
    validate(line)
