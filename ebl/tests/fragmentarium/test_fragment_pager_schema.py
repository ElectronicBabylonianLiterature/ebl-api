from ebl.fragmentarium.application.fragment_pager_info_schema import (
    FragmentPagerInfoSchema,
)
from ebl.fragmentarium.domain.fragment_pager_info import FragmentPagerInfo
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_schema():
    previous = MuseumNumber.of("X.1")
    next = MuseumNumber.of("X.1")
    fragment_info_pager = FragmentPagerInfo(previous, next)
    assert FragmentPagerInfoSchema().dump(fragment_info_pager) == {
        "next": "X.1",
        "previous": "X.1",
    }
