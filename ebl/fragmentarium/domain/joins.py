import attr
from ebl.fragmentarium.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class Join:
    museum_number: MuseumNumber
    is_checked: bool = False
    joined_by: str = ""
    date: str = ""
    note: str = ""
    legacy_data: str = ""
    is_in_fragmentarium: bool = False
