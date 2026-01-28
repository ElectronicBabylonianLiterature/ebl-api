from typing import Sequence

import attr


@attr.s(auto_attribs=True, frozen=True)
class Folio:
    name: str
    number: str

    @property
    def file_name(self):
        return f"{self.name}_{self.number}.jpg"


@attr.s(auto_attribs=True, frozen=True)
class Folios:
    entries: Sequence[Folio] = ()

    def filter(self, user) -> "Folios":
        folios = tuple(
            folio for folio in self.entries if user and user.can_read_folio(folio.name)
        )
        return Folios(folios)
