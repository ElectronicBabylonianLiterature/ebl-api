from ebl.fragmentarium.application.create_line_to_vec import create_line_to_vec
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


def test_create_line_to_vec():
    fragment = TransliteratedFragmentFactory()
    line_to_vec = create_line_to_vec(fragment.text.lines)
    assert fragment.line_to_vec == line_to_vec
