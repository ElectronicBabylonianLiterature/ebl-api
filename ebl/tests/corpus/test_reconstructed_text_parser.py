import pytest  # pyre-ignore[21]

from ebl.corpus.application.reconstructed_text_parser import (
    parse_break,
    parse_lacuna,
    parse_reconstructed_line,
    parse_reconstructed_word,
)
from ebl.corpus.domain.enclosure import (
    BROKEN_OFF_CLOSE,
    BROKEN_OFF_OPEN,
    EMENDATION_CLOSE,
    EMENDATION_OPEN,
    MAYBE_BROKEN_OFF_CLOSE,
    MAYBE_BROKEN_OFF_OPEN,
)
from ebl.corpus.domain.enclosure_validator import validate
from ebl.corpus.domain.reconstructed_text import (
    AkkadianWord,
    Caesura,
    EnclosurePart,
    Lacuna,
    LacunaPart,
    MetricalFootSeparator,
    Modifier,
    SeparatorPart,
    StringPart,
)
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
            [StringPart("ʾABDEGHIKLMNPSTUYZabcdefghiklmnpqrstuwyzÉâêîûāĒēīŠšūṣṭ₄"), []],
        ),
        ("ibnû?", [StringPart("ibnû"), [Modifier.UNCERTAIN]]),
        ("ibnû#", [StringPart("ibnû"), [Modifier.DAMAGED]]),
        ("ibnû!", [StringPart("ibnû"), [Modifier.CORRECTED]]),
        ("ibnû#?", [StringPart("ibnû"), [Modifier.DAMAGED, Modifier.UNCERTAIN]]),
        ("ibnû?#", [StringPart("ibnû"), [Modifier.UNCERTAIN, Modifier.DAMAGED]]),
        (
            "ibnû?#!",
            [
                StringPart("ibnû"),
                [Modifier.UNCERTAIN, Modifier.DAMAGED, Modifier.CORRECTED],
            ],
        ),
        ("ibnû##", [StringPart("ibnû"), [Modifier.DAMAGED]]),
        (
            "[ibnû]",
            [
                EnclosurePart(BROKEN_OFF_OPEN),
                StringPart("ibnû"),
                EnclosurePart(BROKEN_OFF_CLOSE),
                [],
            ],
        ),
        (
            "ib[nû",
            [StringPart("ib"), EnclosurePart(BROKEN_OFF_OPEN), StringPart("nû"), []],
        ),
        (
            "ib]nû",
            [StringPart("ib"), EnclosurePart(BROKEN_OFF_CLOSE), StringPart("nû"), []],
        ),
        (
            "i[b]nû",
            [
                StringPart("i"),
                EnclosurePart(BROKEN_OFF_OPEN),
                StringPart("b"),
                EnclosurePart(BROKEN_OFF_CLOSE),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "ibnû?]",
            [StringPart("ibnû"), EnclosurePart(BROKEN_OFF_CLOSE), [Modifier.UNCERTAIN]],
        ),
        (
            "(ibnû)",
            [
                EnclosurePart(MAYBE_BROKEN_OFF_OPEN),
                StringPart("ibnû"),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                [],
            ],
        ),
        (
            "ib(nû",
            [
                StringPart("ib"),
                EnclosurePart(MAYBE_BROKEN_OFF_OPEN),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "ib)nû",
            [
                StringPart("ib"),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "i(b)nû",
            [
                StringPart("i"),
                EnclosurePart(MAYBE_BROKEN_OFF_OPEN),
                StringPart("b"),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "ibnû#)",
            [
                StringPart("ibnû"),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                [Modifier.DAMAGED],
            ],
        ),
        (
            "[(ibnû)]",
            [
                EnclosurePart(BROKEN_OFF_OPEN),
                EnclosurePart(MAYBE_BROKEN_OFF_OPEN),
                StringPart("ibnû"),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                EnclosurePart(BROKEN_OFF_CLOSE),
                [],
            ],
        ),
        (
            "ib[(nû",
            [
                StringPart("ib"),
                EnclosurePart(BROKEN_OFF_OPEN),
                EnclosurePart(MAYBE_BROKEN_OFF_OPEN),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "ib)]nû",
            [
                StringPart("ib"),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                EnclosurePart(BROKEN_OFF_CLOSE),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "i[(b)]nû",
            [
                StringPart("i"),
                EnclosurePart(BROKEN_OFF_OPEN),
                EnclosurePart(MAYBE_BROKEN_OFF_OPEN),
                StringPart("b"),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                EnclosurePart(BROKEN_OFF_CLOSE),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "[i(b)n]û",
            [
                EnclosurePart(BROKEN_OFF_OPEN),
                StringPart("i"),
                EnclosurePart(MAYBE_BROKEN_OFF_OPEN),
                StringPart("b"),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                StringPart("n"),
                EnclosurePart(BROKEN_OFF_CLOSE),
                StringPart("û"),
                [],
            ],
        ),
        (
            "ibnû?)]",
            [
                StringPart("ibnû"),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                EnclosurePart(BROKEN_OFF_CLOSE),
                [Modifier.UNCERTAIN],
            ],
        ),
        (
            "<ibnû>",
            [
                EnclosurePart(EMENDATION_OPEN),
                StringPart("ibnû"),
                EnclosurePart(EMENDATION_CLOSE),
                [],
            ],
        ),
        (
            "ib<nû",
            [StringPart("ib"), EnclosurePart(EMENDATION_OPEN), StringPart("nû"), []],
        ),
        (
            "ib>nû",
            [StringPart("ib"), EnclosurePart(EMENDATION_CLOSE), StringPart("nû"), []],
        ),
        (
            "i<b>nû",
            [
                StringPart("i"),
                EnclosurePart(EMENDATION_OPEN),
                StringPart("b"),
                EnclosurePart(EMENDATION_CLOSE),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "ibnû?>",
            [StringPart("ibnû"), EnclosurePart(EMENDATION_CLOSE), [Modifier.UNCERTAIN]],
        ),
        ("...ibnû", [LacunaPart(), StringPart("ibnû"), []]),
        ("ibnû...", [StringPart("ibnû"), LacunaPart(), []]),
        ("ib...nû", [StringPart("ib"), LacunaPart(), StringPart("nû"), []]),
        (
            "<...ibnû",
            [EnclosurePart(EMENDATION_OPEN), LacunaPart(), StringPart("ibnû"), []],
        ),
        (
            "ibnû...>",
            [StringPart("ibnû"), LacunaPart(), EnclosurePart(EMENDATION_CLOSE), []],
        ),
        (
            "...>ibnû",
            [LacunaPart(), EnclosurePart(EMENDATION_CLOSE), StringPart("ibnû"), []],
        ),
        (
            "ibnû<...",
            [StringPart("ibnû"), EnclosurePart(EMENDATION_OPEN), LacunaPart(), []],
        ),
        (
            "<...>ibnû",
            [
                EnclosurePart(EMENDATION_OPEN),
                LacunaPart(),
                EnclosurePart(EMENDATION_CLOSE),
                StringPart("ibnû"),
                [],
            ],
        ),
        (
            "ibnû<...>",
            [
                StringPart("ibnû"),
                EnclosurePart(EMENDATION_OPEN),
                LacunaPart(),
                EnclosurePart(EMENDATION_CLOSE),
                [],
            ],
        ),
        (
            "ib<...nû",
            [
                StringPart("ib"),
                EnclosurePart(EMENDATION_OPEN),
                LacunaPart(),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "ib...>nû",
            [
                StringPart("ib"),
                LacunaPart(),
                EnclosurePart(EMENDATION_CLOSE),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "ib<...>nû",
            [
                StringPart("ib"),
                EnclosurePart(EMENDATION_OPEN),
                LacunaPart(),
                EnclosurePart(EMENDATION_CLOSE),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "[<(ibnû)]>",
            [
                EnclosurePart(BROKEN_OFF_OPEN),
                EnclosurePart(EMENDATION_OPEN),
                EnclosurePart(MAYBE_BROKEN_OFF_OPEN),
                StringPart("ibnû"),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                EnclosurePart(BROKEN_OFF_CLOSE),
                EnclosurePart(EMENDATION_CLOSE),
                [],
            ],
        ),
        (
            "ib<[(nû",
            [
                StringPart("ib"),
                EnclosurePart(EMENDATION_OPEN),
                EnclosurePart(BROKEN_OFF_OPEN),
                EnclosurePart(MAYBE_BROKEN_OFF_OPEN),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "ib)]>nû",
            [
                StringPart("ib"),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                EnclosurePart(BROKEN_OFF_CLOSE),
                EnclosurePart(EMENDATION_CLOSE),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "i[<(b)]>nû",
            [
                StringPart("i"),
                EnclosurePart(BROKEN_OFF_OPEN),
                EnclosurePart(EMENDATION_OPEN),
                EnclosurePart(MAYBE_BROKEN_OFF_OPEN),
                StringPart("b"),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                EnclosurePart(BROKEN_OFF_CLOSE),
                EnclosurePart(EMENDATION_CLOSE),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "[i(<b>)n]û",
            [
                EnclosurePart(BROKEN_OFF_OPEN),
                StringPart("i"),
                EnclosurePart(MAYBE_BROKEN_OFF_OPEN),
                EnclosurePart(EMENDATION_OPEN),
                StringPart("b"),
                EnclosurePart(EMENDATION_CLOSE),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                StringPart("n"),
                EnclosurePart(BROKEN_OFF_CLOSE),
                StringPart("û"),
                [],
            ],
        ),
        (
            "ibnû?)>]",
            [
                StringPart("ibnû"),
                EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                EnclosurePart(EMENDATION_CLOSE),
                EnclosurePart(BROKEN_OFF_CLOSE),
                [Modifier.UNCERTAIN],
            ],
        ),
        ("ib-nû", [StringPart("ib"), SeparatorPart(), StringPart("nû"), []]),
        ("...-nû", [LacunaPart(), SeparatorPart(), StringPart("nû"), []]),
        ("ib-...", [StringPart("ib"), SeparatorPart(), LacunaPart(), []]),
        (
            "...]-nû",
            [
                LacunaPart(),
                EnclosurePart(BROKEN_OFF_CLOSE),
                SeparatorPart(),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "ib-[...",
            [
                StringPart("ib"),
                SeparatorPart(),
                EnclosurePart(BROKEN_OFF_OPEN),
                LacunaPart(),
                [],
            ],
        ),
        (
            "ib[-nû",
            [
                StringPart("ib"),
                EnclosurePart(BROKEN_OFF_OPEN),
                SeparatorPart(),
                StringPart("nû"),
                [],
            ],
        ),
        (
            "ib-]nû",
            [
                StringPart("ib"),
                SeparatorPart(),
                EnclosurePart(BROKEN_OFF_CLOSE),
                StringPart("nû"),
                [],
            ],
        ),
    ],
)
def test_word(text, expected):
    assert parse_reconstructed_word(text) == AkkadianWord(
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
def test_invalid_word(text):
    assert_parse_error(parse_reconstructed_word, text)


@pytest.mark.parametrize(
    "text,before,after",
    [
        ("...", tuple(), tuple()),
        ("[...", (BROKEN_OFF_OPEN,), tuple()),
        ("...]", tuple(), (BROKEN_OFF_CLOSE,)),
        ("[...]", (BROKEN_OFF_OPEN,), (BROKEN_OFF_CLOSE,)),
        ("(...", (MAYBE_BROKEN_OFF_OPEN,), tuple()),
        ("...)", tuple(), (MAYBE_BROKEN_OFF_CLOSE,)),
        ("(...)", (MAYBE_BROKEN_OFF_OPEN,), (MAYBE_BROKEN_OFF_CLOSE,)),
        ("[(...", (BROKEN_OFF_OPEN, MAYBE_BROKEN_OFF_OPEN), tuple()),
        ("...)]", tuple(), (MAYBE_BROKEN_OFF_CLOSE, BROKEN_OFF_CLOSE)),
        (
            "[(...)]",
            (BROKEN_OFF_OPEN, MAYBE_BROKEN_OFF_OPEN),
            (MAYBE_BROKEN_OFF_CLOSE, BROKEN_OFF_CLOSE),
        ),
    ],
)
def test_lacuna(text, before, after):
    assert parse_lacuna(text) == Lacuna(before, after)


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
def test_invalid_lacuna(text):
    assert_parse_error(parse_lacuna, text)


@pytest.mark.parametrize("text,is_uncertain", [("||", False), ("(||)", True)])
def test_caesura(text, is_uncertain):
    assert parse_break(text) == Caesura(is_uncertain)


@pytest.mark.parametrize("text,is_uncertain", [("|", False), ("(|)", True)])
def test_feet_separator(text, is_uncertain):
    assert parse_break(text) == MetricalFootSeparator(is_uncertain)


@pytest.mark.parametrize("text", ["|||", "||||", "[|]", "[(|)]", "[||]", "[(||)]"])
def test_invalid_break(text):
    assert_parse_error(parse_break, text)


WORD = AkkadianWord((StringPart("ibnû"),))


@pytest.mark.parametrize(
    "text,expected",
    [
        ("ibnû", (WORD,)),
        ("...", (Lacuna(tuple(), tuple()),)),
        ("... ibnû", (Lacuna(tuple(), tuple()), WORD)),
        ("ibnû ...", (WORD, Lacuna(tuple(), tuple()))),
        ("[...] ibnû", (Lacuna((BROKEN_OFF_OPEN,), (BROKEN_OFF_CLOSE,)), WORD)),
        ("ibnû [...]", (WORD, Lacuna((BROKEN_OFF_OPEN,), (BROKEN_OFF_CLOSE,)))),
        ("...ibnû", (AkkadianWord((LacunaPart(), StringPart("ibnû"))),)),
        ("ibnû...", (AkkadianWord((StringPart("ibnû"), LacunaPart())),)),
        (
            "ib...nû",
            (AkkadianWord((StringPart("ib"), LacunaPart(), StringPart("nû"))),),
        ),
        ("ibnû | ibnû", (WORD, MetricalFootSeparator(False), WORD)),
        ("ibnû (|) ibnû", (WORD, MetricalFootSeparator(True), WORD)),
        ("ibnû || ibnû", (WORD, Caesura(False), WORD)),
        ("ibnû (||) ibnû", (WORD, Caesura(True), WORD)),
    ],
)
def test_reconstructed_line(text, expected):
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
def test_invalid_reconstructed_line(text):
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
def test_validate_invalid(text):
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
def test_validate_valid(text):
    line = parse_reconstructed_line(text)
    validate(line)
