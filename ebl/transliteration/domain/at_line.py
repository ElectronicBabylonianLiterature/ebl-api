from abc import abstractmethod
from enum import Enum
from functools import singledispatchmethod  # type: ignore
from typing import Optional, Union, Sequence

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
    def _content_as_is(self) -> Sequence[Token]:
        ...

    @property
    def content(self) -> Sequence[Token]:
        return (ValueToken(self._content_as_is[0].value),)


@attr.s(auto_attribs=True, frozen=True)
class SealAtLine(AtLine):
    number: int

    @property
    def _content_as_is(self):
        return (ValueToken(f"seal {self.number}"),)


@attr.s(auto_attribs=True, frozen=True)
class HeadingAtLine(AtLine):
    number: int

    @property
    def _content_as_is(self):
        return (ValueToken(f"h{self.number}"),)


@attr.s(auto_attribs=True, frozen=True)
class ColumnAtLine(AtLine):
    column_label: ColumnLabel

    @property
    def _content_as_is(self):
        return (
            ValueToken(
                f"column {self.column_label.column}{''.join([status.value for status in self.column_label.status])}"
            ),
        )


@attr.s(auto_attribs=True, frozen=True)
class DiscourseAtLine(AtLine):
    discourse_label: atf.Discourse

    @property
    def _content_as_is(self):
        return (ValueToken(f"{self.discourse_label.value}"),)


@attr.s(auto_attribs=True, frozen=True)
class SurfaceAtLine(AtLine):
    surface_label: SurfaceLabel

    @property
    def _content_as_is(self):
        return (
            ValueToken(
                f"{self.surface_label.surface.value[0]}{' '+self.surface_label.text if self.surface_label.text else '' }{self.surface_label._status_string}"
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
    def _content_as_is(self):
        return (
            ValueToken(
                f"{self.object_label.value}{' ' + self.text if self.text else ''}{self._status_string}"
            ),
        )
