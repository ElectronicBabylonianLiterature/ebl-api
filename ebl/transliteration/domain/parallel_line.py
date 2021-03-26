from abc import abstractmethod
from enum import Enum, unique
from typing import Optional, Tuple, cast

import attr

from ebl.corpus.domain.stage import Stage
from ebl.corpus.domain.text_id import TextId
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_number import AbstractLineNumber


@unique
class Genre(Enum):
    LITERATURE = "L"


@attr.s(auto_attribs=True, frozen=True)
class ChapterName:
    stage: Stage
    version: str
    name: str

    def __str__(self) -> str:
        version = f'"{self.version}" ' if self.version else ""
        name = f'"{self.name}"'
        return f"{self.stage.abbreviation} {version}{name}"


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
    surface: Optional[SurfaceLabel]
    line_number: AbstractLineNumber

    @property
    def display_value(self) -> str:
        cf = "cf. " if self.has_cf else ""
        duplicates = "&d " if self.has_duplicates else ""
        surface = (
            ""
            if self.surface is None
            else f"{cast(SurfaceLabel, self.surface).to_value()} "
        )
        line_number = self.line_number.label
        return f"{cf}F {self.museum_number} {duplicates}{surface}{line_number}"


@attr.s(auto_attribs=True, frozen=True)
class ParallelText(ParallelLine):
    genre: Genre
    text: TextId
    chapter: Optional[ChapterName]
    line_number: AbstractLineNumber

    @property
    def display_value(self) -> str:
        cf = "cf. " if self.has_cf else ""
        genre = self.genre.value
        chapter = "" if self.chapter is None else f"{self.chapter} "
        line_number = self.line_number.label
        return f"{cf}{genre} {self.text} {chapter}{line_number}"


@attr.s(auto_attribs=True, frozen=True)
class ParallelComposition(ParallelLine):
    name: str
    line_number: AbstractLineNumber

    @property
    def display_value(self) -> str:
        cf = "cf. " if self.has_cf else ""
        line_number = self.line_number.label
        return f"{cf}({self.name} {line_number})"
