from abc import abstractmethod
from typing import Optional, Sequence, Tuple

import attr

from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.labels import (
    ColumnLabel,
    Label,
    ObjectLabel,
    SurfaceLabel,
)
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId


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
    def display_value(self) -> str: ...

    @property
    def atf(self) -> Atf:
        return Atf(f"// {self.display_value}")

    @property
    def lemmatization(self) -> Tuple[LemmatizationToken]:
        return (LemmatizationToken(self.display_value),)


@attr.s(auto_attribs=True, frozen=True)
class Labels:
    object: Optional[ObjectLabel] = None
    surface: Optional[SurfaceLabel] = None
    column: Optional[ColumnLabel] = None

    @property
    def all(self) -> Sequence[Label]:
        return tuple(
            label
            for label in [self.object, self.surface, self.column]
            if label is not None
        )

    def __str__(self) -> str:
        return " ".join(label.to_value() for label in self.all)


@attr.s(auto_attribs=True, frozen=True)
class ParallelFragment(ParallelLine):
    museum_number: MuseumNumber
    has_duplicates: bool
    labels: Labels
    line_number: AbstractLineNumber
    exists: Optional[bool] = None

    @property
    def display_value(self) -> str:
        cf = "cf. " if self.has_cf else ""
        duplicates = "&d " if self.has_duplicates else ""
        labels = f"{self.labels} " if self.labels.all else ""
        line_number = self.line_number.label
        return f"{cf}F {self.museum_number} {duplicates}{labels}{line_number}"


@attr.s(auto_attribs=True, frozen=True)
class ParallelText(ParallelLine):
    text: TextId
    chapter: Optional[ChapterName]
    line_number: AbstractLineNumber
    exists: Optional[bool] = None
    implicit_chapter: Optional[ChapterName] = None

    @property
    def display_value(self) -> str:
        cf = "cf. " if self.has_cf else ""
        chapter = "" if self.chapter is None else f"{self.chapter} "
        line_number = self.line_number.label
        return f"{cf}{self.text} {chapter}{line_number}"


@attr.s(auto_attribs=True, frozen=True)
class ParallelComposition(ParallelLine):
    name: str
    line_number: AbstractLineNumber

    @property
    def display_value(self) -> str:
        cf = "cf. " if self.has_cf else ""
        line_number = self.line_number.label
        return f"{cf}({self.name} {line_number})"
