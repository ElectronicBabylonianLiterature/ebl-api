import pytest  # pyre-ignore[21]

from ebl.fragmentarium.application.line_to_vec_updater import create_line_to_vec
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


def test_line_to_vec_updater():
    fragment = TransliteratedFragmentFactory()
    line_to_vec = create_line_to_vec(fragment.text.lines)
    assert fragment.line_to_vec == line_to_vec
