from typing import Optional, Sequence
import attr
import pydash
from ebl.transliteration.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class Join:
    museum_number: MuseumNumber
    is_checked: bool = False
    is_envelope: bool = False
    joined_by: str = ""
    date: str = ""
    note: str = ""
    legacy_data: str = ""
    is_in_fragmentarium: bool = False


@attr.s(auto_attribs=True, frozen=True)
class Joins:
    _fragments: Sequence[Sequence[Join]] = ()

    @property
    def fragments(self) -> Sequence[Sequence[Join]]:
        return sorted(
            (sorted(group) for group in self._fragments),
            key=lambda group: min(join.museum_number for join in group),
        )

    @property
    def lowest(self) -> Optional[MuseumNumber]:
        return (
            pydash.chain(self._fragments)
            .flatten()
            .filter("is_in_fragmentarium")
            .map("museum_number")
            .sort()
            .head()
            .value()
        )
