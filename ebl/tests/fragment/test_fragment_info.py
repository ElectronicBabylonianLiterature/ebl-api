from ebl.fragment.fragment_info import FragmentInfo
from ebl.tests.factories.fragment import FragmentFactory


FRAGMENT = FragmentFactory.build()


def test_of():
    matching_lines = (('1. kur', ), )
    assert FragmentInfo.of(FRAGMENT, matching_lines) == FragmentInfo(
        FRAGMENT.number,
        FRAGMENT.accession,
        FRAGMENT.script,
        FRAGMENT.description,
        matching_lines
    )


def test_of_defaults():
    assert FragmentInfo.of(FRAGMENT).matching_lines == tuple()
