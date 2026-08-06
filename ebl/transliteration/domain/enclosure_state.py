from typing import FrozenSet

import attr

from ebl.transliteration.domain.enclosure_error import EnclosureError
from ebl.transliteration.domain.enclosure_type import EnclosureType


@attr.s(auto_attribs=True, frozen=True)
class EnclosureVisitorState:
    enclosures: FrozenSet[EnclosureType] = frozenset()

    @property
    def has_enclosures(self) -> int:
        return len(self.enclosures) > 0

    def is_open(self, enclosure: EnclosureType) -> bool:
        return enclosure in self.enclosures

    def open(self, enclosure: EnclosureType) -> "EnclosureVisitorState":
        if self._is_allowed_to_open(enclosure):
            return EnclosureVisitorState(self.enclosures.union({enclosure}))
        else:
            raise EnclosureError()

    def close(self, enclosure: EnclosureType) -> "EnclosureVisitorState":
        if self._is_allowed_to_close(enclosure):
            return EnclosureVisitorState(self.enclosures.difference({enclosure}))
        else:
            raise EnclosureError()

    def _is_allowed_to_open(self, enclosure: EnclosureType) -> bool:
        return enclosure.does_not_forbid(
            self.enclosures
        ) and enclosure.are_requirements_satisfied_by(self.enclosures)

    def _is_allowed_to_close(self, enclosure: EnclosureType) -> bool:
        return self.is_open(enclosure) and not self._is_required(enclosure)

    def _is_required(self, enclosure: EnclosureType) -> bool:
        required = {
            required_type
            for open_ in self.enclosures
            for required_type in open_.required
        }
        return enclosure in required
