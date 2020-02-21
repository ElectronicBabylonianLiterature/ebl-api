import pytest

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.at_line import AtLine, Seal, Column, Heading


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        ("@h1!", [AtLine(Heading(1), atf.Status.CORRECTION, "")]),
        ("@h 1!", [AtLine(Heading(1), atf.Status.CORRECTION, "")]),
        ("@h1", [AtLine(Heading(1), None, "")]),
        ("@h 1", [AtLine(Heading(1), None, "")]),
        ("@column 1", [AtLine(Column(1), None, "")]),
        ("@seal 1", [AtLine(Seal(1), None, "")]),
        ("@seal 101!", [AtLine(Seal(101), atf.Status.CORRECTION, "")]),
        ("@fragment a !", [AtLine(atf.Object.FRAGMENT, atf.Status.CORRECTION, "a")]),
        ("@fragment a!", [AtLine(atf.Object.FRAGMENT, atf.Status.CORRECTION, "a")]),
        ("@object Stone wig", [AtLine(atf.Object.OBJECT, None, "Stone wig")]),
        (
            "@object Stone wig!",
            [AtLine(atf.Object.OBJECT, atf.Status.CORRECTION, "Stone wig")],
        ),
        ("@reverse !", [AtLine(atf.Surface.REVERSE, atf.Status.CORRECTION)]),
        ("@surface a !", [AtLine(atf.Surface.SURFACE, atf.Status.CORRECTION, "a")]),
        ("@object what !", [AtLine(atf.Object.OBJECT, atf.Status.CORRECTION, "what")]),
        ("@tablet !", [AtLine(atf.Object.TABLET, atf.Status.CORRECTION)]),
        ("@face a !", [AtLine(atf.Surface.FACE, atf.Status.CORRECTION, "a")]),
        ("@edge c !", [AtLine(atf.Surface.EDGE, atf.Status.CORRECTION, "c")]),
        ("@prism !", [AtLine(atf.Object.PRISM, atf.Status.CORRECTION, "")]),
        ("@object seal!", [AtLine(atf.Object.OBJECT, atf.Status.CORRECTION, "seal")]),
    ],
)
def test_parse_atf_at_line(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines
