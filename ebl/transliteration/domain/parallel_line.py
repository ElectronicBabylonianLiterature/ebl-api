from abc import abstractmethod
from typing import cast, Optional, Tuple

import attr

from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.lemmatization import LemmatizationToken
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.atf import Surface


@attr.s(auto_attribs=True, frozen=True)
class ParallelLine(Line):
    has_cf: bool

    @property
    @abstractmethod
    def display_value(self) -> str:
        ...

    @property
    def atf(self) -> Atf:
        return Atf(f"// {self.display_value}")

    @property
    def lemmatization(self) -> Tuple[LemmatizationToken]:
        return (LemmatizationToken(self.display_value),)


@attr.s(auto_attribs=True, frozen=True)
class ParallelFragment(ParallelLine):
    museum_number: MuseumNumber
    has_duplicates: bool
    surface: Optional[Surface]
    line_number: AbstractLineNumber

    @property
    def display_value(self) -> str:
        cf = "cf. " if self.has_cf else ""
        duplicates = "&d " if self.has_duplicates else ""
        surface = (
            "" if self.surface is None else f"{cast(Surface, self.surface).label} "
        )
        line_number = self.line_number.label
        return f"{cf}{self.museum_number} {duplicates}{surface}{line_number}"
