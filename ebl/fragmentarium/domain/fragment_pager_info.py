import attr

from ebl.transliteration.domain.museum_number import MuseumNumber


@attr.s(frozen=True, auto_attribs=True)
class FragmentPagerInfo:
    previous: MuseumNumber
    next: MuseumNumber
