import pytest

from ebl.fragmentarium.application.matches.create_line_to_vec import (
    create_line_to_vec,
    LineToVecEncoding,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.lark_parser import parse_atf_lark


@pytest.mark.parametrize(
    "atf",
    [
        [
            "1'. x [...]\n@colophon\n2'. x [...]",
            (LineToVecEncoding.from_list([1, 2]),),
        ],
        [
            "1'. x [...]\n@column 1\n2'. x [...]",
            (LineToVecEncoding.from_list([1, 2]),),
        ],
        [
            "1'. x [...]\n@column 2\n1'. x [...]",
            (LineToVecEncoding.from_list([1]), LineToVecEncoding.from_list([1])),
        ],
        [
            "1'. x [...]\n@obverse\n2'. x [...]",
            (LineToVecEncoding.from_list([1, 2]),),
        ],
        [
            "1'. x [...]\n@obverse\n1'. x [...]",
            (LineToVecEncoding.from_list([1]), LineToVecEncoding.from_list([1])),
        ],
        [
            "@obverse\n1'. x [...]\n@obverse\n1'. x [...]\n2'. x [...]\n@edge\n1'. x [...]",
            (LineToVecEncoding.from_list([1]), LineToVecEncoding.from_list([1, 2]), LineToVecEncoding.from_list([1])),
        ],
        [
            "1'. x [...]\n$ end of side\n1'. x [...]",
            (LineToVecEncoding.from_list([1, 5]), LineToVecEncoding.from_list([1])),
        ],
    ],
)
def test_create_line_to_vec_1(atf, transliteration_factory):
    transliteration = parse_atf_lark(atf[0])
    #line_to_vec = create_line_to_vec(transliteration)
    #assert line_to_vec == line_to_vec


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
