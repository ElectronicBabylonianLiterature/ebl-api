from abc import abstractmethod
from enum import Enum
from typing import Optional, Union, Tuple

import attr

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.tokens import ValueToken, Token


@attr.s(auto_attribs=True, frozen=True)
class DollarLine(Line):
    @property
    def prefix(self):
        return "$"

    @property
    @abstractmethod
    def _content_value(self) -> str:
        ...

    @property
    def content(self) -> Tuple[Token]:
        return (ValueToken.of(f" {self._content_value}"),)


@attr.s(auto_attribs=True, frozen=True)
class SealDollarLine(DollarLine):
    number: int

    @property
    def _content_value(self):
        return f"seal {self.number}"


@attr.s(auto_attribs=True, frozen=True)
class LooseDollarLine(DollarLine):
    text: str = ""

    @property
    def _content_value(self) -> str:
        return f"({self.text})"


@attr.s(auto_attribs=True, frozen=True)
class ImageDollarLine(DollarLine):
    number: str = ""
    letter: Optional[str] = ""
    text: str = ""

    @property
    def _content_value(self) -> str:
        letter = self.letter or ""
        return f"(image {self.number}{letter} = {self.text})"


@attr.s(auto_attribs=True, frozen=True)
class RulingDollarLine(DollarLine):
    number: atf.Ruling
    status: Optional[atf.DollarStatus] = None

    @property
    def _content_value(self) -> str:
        status = f" {self.status.value}" if self.status else ""
        return f"{self.number.value} ruling{status}"


@attr.s(frozen=True)
class ScopeContainer:
    content: Union[atf.Surface, atf.Scope, atf.Object] = attr.ib()
    text: str = attr.ib(default="")

    @text.validator
    def _check_text(self, attribute, value):
        if value and self.content not in [
            atf.Object.OBJECT,
            atf.Surface.SURFACE,
            atf.Object.FRAGMENT,
            atf.Surface.FACE,
            atf.Surface.EDGE,
        ]:
            raise ValueError(
                "non-empty string only allowed if the content is "
                "'atf.OBJECT.OBJECT' or 'atf.SURFACE.SURACE'"
            )

    @property
    def value(self):
        text = f" {self.text}" if self.text else ""
        content_value = ScopeContainer.to_value(self.content)
        return f"{content_value}{text}"

    @staticmethod
    def to_value(enum) -> str:
        if isinstance(enum, atf.Surface):
            return enum.atf
        else:
            return enum.value


@attr.s(auto_attribs=True, frozen=True)
class StateDollarLine(DollarLine):
    Range = Tuple[int, int]
    qualification: Optional[atf.Qualification]
    extent: Optional[Union[atf.Extent, int, Range]]
    scope: Optional[ScopeContainer]
    state: Optional[atf.State]
    status: Optional[atf.DollarStatus]

    @property
    def _content_value(self) -> str:
        return " ".join(
            [
                StateDollarLine.to_atf(x)
                for x in [
                    self.qualification,
                    self.extent,
                    self.scope,
                    self.state,
                    self.status,
                ]
                if x
            ]
        )

    @staticmethod
    def to_atf(column) -> str:
        if isinstance(column, tuple):
            return f"{column[0]}-{column[1]}"
        elif isinstance(column, Enum):
            return column.value
        elif isinstance(column, ScopeContainer):
            return column.value
        else:
            return str(column)
