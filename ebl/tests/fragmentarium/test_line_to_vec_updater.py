from ebl.fragmentarium.domain.fragment import LineToVec
from ebl.fragmentarium.matching_fragments.line_to_vec_updater import create_line_to_vec
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.lark_parser import parse_atf_lark


def test_line_to_vec_updater_prefix():
    atf = """A+1. %sux x [...] x x x [...]
2'. ($___$) mu x [x (x)] mar-kas AN-e K[I?-ti₃? ...]
3'. %sux u₄ gi₆! mu₂-mu₂-da x [...]
4'. ($___$) ba-nu-u u₄-mu u mu-šu [...]
    """
    lines = parse_atf_lark(atf)
    assert create_line_to_vec(lines) == ()


def test_line_to_vec_updater():
    fragment = TransliteratedFragmentFactory()
    line_to_vec = create_line_to_vec(fragment.text.lines)
    assert fragment.line_to_vec == LineToVec(line_to_vec)
