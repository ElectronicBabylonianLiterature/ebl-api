from ebl.fragmentarium.application.create_line_to_vec import (
    create_line_to_vec,
    LineToVecEncoding,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


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
