from ebl.fragmentarium.domain.fragment import LineToVec
from ebl.fragmentarium.matching_fragments.line_to_vec_updater import create_line_to_vec
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


def test_line_to_vec_updater():
    fragment = TransliteratedFragmentFactory()
    line_to_vec = create_line_to_vec(fragment.text.lines)
    assert fragment.line_to_vec == LineToVec(line_to_vec)
