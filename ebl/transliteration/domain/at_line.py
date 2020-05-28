from abc import abstractmethod
from typing import Sequence, Optional, Tuple

import attr

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf import Status
from ebl.transliteration.domain.labels import (
    SurfaceLabel,
    ColumnLabel,
    no_duplicate_status,
)
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.tokens import ValueToken, Token


@attr.s(auto_attribs=True, frozen=True)
class AtLine(Line):
    @property
    def prefix(self):
        return "@"

    @property
    @abstractmethod
    def display_value(self) -> str:
        ...

    @property
    def content(self) -> Tuple[Token]:
        return (ValueToken.of(f"{self.display_value}"),)


@attr.s(auto_attribs=True, frozen=True)
class SealAtLine(AtLine):
    number: int

    @property
    def display_value(self):
        return f"seal {self.number}"


@attr.s(auto_attribs=True, frozen=True)
class HeadingAtLine(AtLine):
    number: int

    @property
    def display_value(self):
        return f"h{self.number}"


@attr.s(auto_attribs=True, frozen=True)
class ColumnAtLine(AtLine):
    column_label: ColumnLabel

    @property
    def display_value(self):
        return f"column {self.column_label.column}{self.column_label._status_string}"


@attr.s(auto_attribs=True, frozen=True)
class DiscourseAtLine(AtLine):
    discourse_label: atf.Discourse

    @property
    def display_value(self):
        return f"{self.discourse_label.value}"


@attr.s(auto_attribs=True, frozen=True)
class SurfaceAtLine(AtLine):
    surface_label: SurfaceLabel

    @property
    def display_value(self):
        text = f" {self.surface_label.text}" if self.surface_label.text else ""
        return f"{self.surface_label.surface.value[0]}{text}{self.surface_label._status_string}"


@attr.s(auto_attribs=True, frozen=True)
class ObjectAtLine(AtLine):
    status: Sequence[Status] = attr.ib(validator=no_duplicate_status)
    object_label: atf.Object
    text: str = attr.ib(default="")

    @text.validator
    def _check_text(self, attribute, value):
        if value and self.object_label not in [
            atf.Object.OBJECT,
            atf.Object.FRAGMENT,
        ]:
            raise ValueError(
                "non-empty string only allowed if the content is 'atf.OBJECT.OBJECT'"
            )

    @property
    def _status_string(self):
        return "".join(status.value for status in self.status)

    @property
    def display_value(self):
        text = f" {self.text}" if self.text else ""
        return f"{self.object_label.value}{text}{self._status_string}"


@attr.s(auto_attribs=True, frozen=True)
class DivisionAtLine(AtLine):
    text: str
    number: Optional[int] = None

    @property
    def display_value(self):
        number = f" {str(self.number)}" if self.number else ""
        return f"m=division {self.text}{number}"


@attr.s(auto_attribs=True, frozen=True)
class CompositeAtLine(AtLine):
    composite: atf.Composite
    text: str
    number: Optional[int] = attr.ib(default=None)

    @number.validator
    def _check_text(self, attribute, value):
        if value is not None and self.composite == atf.Composite.END:
            raise ValueError("number only allowed with '@end' composite")

    @property
    def display_value(self):
        number = f" {str(self.number)}" if self.number else ""
        text = f" {str(self.text)}" if self.text else ""
        return f"{self.composite.value}{text}{number}"
