import pytest

from ebl.fragmentarium.application.matches.create_line_to_vec import (
    create_line_to_vec,
    split_lines,
)
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncoding
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.lark_parser import parse_atf_lark


@pytest.mark.parametrize(
    "atf, expected",
    [
        [
            "1'-2'. [x x x x x x x x] x na-aš₂-al;-[b]a pu-ti-ka",
            (LineToVecEncoding.from_list([1, 1]),),
        ],
        [
            "1-2. [x x x x x x x x] x na-aš₂-al;-[b]a pu-ti-ka",
            (LineToVecEncoding.from_list([0, 1, 1]),),
        ],
        [
            "1-2. [x x x x x x x x] x na-aš₂-al;-[b]a pu-ti-ka\n1'. [...]",
            (LineToVecEncoding.from_list([0, 1, 1]), LineToVecEncoding.from_list([1])),
        ],
        [
            "1. x [...]\n@colophon\n2. x [...]",
            (LineToVecEncoding.from_list([0, 1, 1]),),
        ],
        ["1'. x [...]\n@colophon\n2'. x [...]", (LineToVecEncoding.from_list([1, 1]),)],
        [
            "1. x [...]\n@column 1\n2. x [...]",
            (LineToVecEncoding.from_list([0, 1, 1]),),
        ],
        ["1'. x [...]\n@obverse\n2'. x [...]", (LineToVecEncoding.from_list([1, 1]),)],
        [
            "1'. x [...]\n@obverse\n1'. x [...]",
            (LineToVecEncoding.from_list([1]), LineToVecEncoding.from_list([1])),
        ],
        [
            "1. x [...]\n@obverse\n1. x [...]",
            (LineToVecEncoding.from_list([0, 1]), LineToVecEncoding.from_list([0, 1])),
        ],
        [
            "@obverse\n1'. x [...]\n@reverse\n1'. x [...]\n2'. x [...]\n@edge\n1'. x [...]",
            (
                LineToVecEncoding.from_list([1]),
                LineToVecEncoding.from_list([1, 1]),
                LineToVecEncoding.from_list([1]),
            ),
        ],
        [
            "1. x [...]\n2. x [...]\n$ end of side\n1'. x [...]",
            (
                LineToVecEncoding.from_list([0, 1, 1, 5]),
                LineToVecEncoding.from_list([1]),
            ),
        ],
    ],
)
def test_create_line_to_vec_from_atf(atf, expected, transliteration_factory):
    lines = parse_atf_lark(atf).lines
    assert create_line_to_vec(lines) == expected


@pytest.mark.parametrize(
    "atf, expected",
    [
        ["1'. x [...]\n@colophon\n2'. x [...]", [3, 3]],
        ["1'. x [...]\n@column 2\n1'. x [...]", [2, 2]],
        ["1'. x [...]\n@obverse\n2'. x [...]", [3, 3]],
        ["1'. x [...]\n@obverse\n1'. x [...]", [2, 2]],
        ["1. x [...]\n2. x [...]\n$ end of side\n1'. x [...]", [3, 3]],
    ],
)
def test_split_lines(atf, expected):
    lines = parse_atf_lark(atf).lines
    splitted_lines = tuple(
        line for line in [lines[: expected[0]], lines[expected[1] :]] if len(line)
    )

    assert split_lines(lines) == splitted_lines


def test_split_multiple_lines():
    lines = parse_atf_lark(
        "@obverse\n1'. x [...]\n@reverse\n1'. x [...]\n2'. x [...]\n@edge\n1'. x [...]"
    ).lines
    splitted_lines = (lines[:3], lines[3:6], lines[6:])
    assert split_lines(lines) == splitted_lines


def test_create_line_to_vec():
    fragment = TransliteratedFragmentFactory()
    line_to_vec = create_line_to_vec(fragment.text.lines)
    assert fragment.line_to_vec == line_to_vec


def test_line_to_vec_encoding_from_list():
    assert (
        LineToVecEncoding(0),
        LineToVecEncoding(1),
        LineToVecEncoding(2),
        LineToVecEncoding(3),
        LineToVecEncoding(4),
        LineToVecEncoding(5),
    ) == LineToVecEncoding.from_list([0, 1, 2, 3, 4, 5])
