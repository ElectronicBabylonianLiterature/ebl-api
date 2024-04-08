from abc import abstractmethod
from typing import Optional, Sequence, Tuple

import attr

from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.atf import Atf, Composite, Discourse
from ebl.transliteration.domain.labels import SurfaceLabel, ColumnLabel, ObjectLabel
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.markup import convert_part_sequence, MarkupPart


@attr.s(auto_attribs=True, frozen=True)
class AtLine(Line):
    @property
    @abstractmethod
    def display_value(self) -> str: ...

    @property
    def atf(self) -> Atf:
        return Atf(f"@{self.display_value}")

    @property
    def lemmatization(self) -> Tuple[LemmatizationToken]:
        return (LemmatizationToken(self.display_value),)


@attr.s(auto_attribs=True, frozen=True)
class SealAtLine(AtLine):
    number: int

    @property
    def display_value(self) -> str:
        return f"seal {self.number}"


@attr.s(auto_attribs=True, frozen=True)
class HeadingAtLine(AtLine):
    number: int
    parts: Sequence[MarkupPart] = attr.ib(
        converter=convert_part_sequence, default=tuple()
    )

    @property
    def display_value(self) -> str:
        parts = f" {''.join(part.value for part in self.parts)}" if self.parts else ""
        return f"h{self.number}{parts}"


@attr.s(auto_attribs=True, frozen=True)
class ColumnAtLine(AtLine):
    column_label: ColumnLabel

    @property
    def display_value(self) -> str:
        return f"column {self.column_label.column}{self.column_label.status_string}"


@attr.s(auto_attribs=True, frozen=True)
class DiscourseAtLine(AtLine):
    discourse_label: Discourse

    @property
    def display_value(self) -> str:
        return f"{self.discourse_label.value}"


@attr.s(auto_attribs=True, frozen=True)
class SurfaceAtLine(AtLine):
    surface_label: SurfaceLabel

    @property
    def display_value(self) -> str:
        text = f" {self.surface_label.text}" if self.surface_label.text else ""
        return (
            f"{self.surface_label.surface.atf}{text}{self.surface_label.status_string}"
        )


@attr.s(auto_attribs=True, frozen=True)
class ObjectAtLine(AtLine):
    label: ObjectLabel

    @property
    def display_value(self) -> str:
        text = f" {self.label.text}" if self.label.text else ""
        return f"{self.label.object.value}{text}{self.label.status_string}"


@attr.s(auto_attribs=True, frozen=True)
class DivisionAtLine(AtLine):
    text: str
    number: Optional[int] = None

    @property
    def display_value(self) -> str:
        number = f" {str(self.number)}" if self.number else ""
        return f"m=division {self.text}{number}"


@attr.s(auto_attribs=True, frozen=True)
class CompositeAtLine(AtLine):
    composite: Composite
    text: str
    number: Optional[int] = attr.ib(default=None)

    @number.validator
    def _check_text(self, attribute, value) -> None:
        if value is not None and self.composite == Composite.END:
            raise ValueError("number only allowed with '@end' composite")

    @property
    def display_value(self) -> str:
        number = f" {str(self.number)}" if self.number else ""
        text = f" {str(self.text)}" if self.text else ""
        return f"{self.composite.value}{text}{number}"
