from abc import abstractmethod
from typing import Sequence, Optional

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
    def content(self) -> Sequence[Token]:
        ...


@attr.s(auto_attribs=True, frozen=True)
class SealAtLine(AtLine):
    number: int

    @property
    def content(self):
        return (ValueToken(f"seal {self.number}"),)


@attr.s(auto_attribs=True, frozen=True)
class HeadingAtLine(AtLine):
    number: int

    @property
    def content(self):
        return (ValueToken(f"h{self.number}"),)


@attr.s(auto_attribs=True, frozen=True)
class ColumnAtLine(AtLine):
    column_label: ColumnLabel

    @property
    def content(self):
        return (
            ValueToken(
                f"column {self.column_label.column}"
                f"{''.join([status.value for status in self.column_label.status])}"
            ),
        )


@attr.s(auto_attribs=True, frozen=True)
class DiscourseAtLine(AtLine):
    discourse_label: atf.Discourse

    @property
    def content(self):
        return (ValueToken(f"{self.discourse_label.value}"),)


@attr.s(auto_attribs=True, frozen=True)
class SurfaceAtLine(AtLine):
    surface_label: SurfaceLabel

    @property
    def content(self):
        return (
            ValueToken(
                f"{self.surface_label.surface.value[0]}"
                f"{' '+self.surface_label.text if self.surface_label.text else '' }"
                f"{self.surface_label._status_string}"
            ),
        )


@attr.s(auto_attribs=True, frozen=True)
class ObjectAtLine(AtLine):
    status: Sequence[Status] = attr.ib(validator=no_duplicate_status)
    object_label: atf.Object
    text: str = ""

    @property
    def _status_string(self):
        return "".join([status.value for status in self.status])

    @property
    def content(self):
        return (
            ValueToken(
                f"{self.object_label.value}"
                f"{' ' + self.text if self.text else ''}"
                f"{self._status_string}"
            ),
        )


@attr.s(auto_attribs=True, frozen=True)
class DivisionAtLine(AtLine):
    text: str
    number: Optional[int] = None

    @property
    def content(self):
        return (
            ValueToken(
                f"m=division {self.text}{' ' + str(self.number) if self.number else ''}"
            ),
        )


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
    def content(self):
        return (
            ValueToken(
                f"{self.composite.value} "
                f"{self.text}{' ' + str(self.number) if self.number else ''}"
            ),
        )
