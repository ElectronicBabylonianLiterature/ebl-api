from abc import abstractmethod
from enum import Enum
from functools import singledispatchmethod  # type: ignore
from typing import Optional, Sequence, Tuple, Union

import attr

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.tokens import Token, ValueToken


@attr.s(auto_attribs=True, frozen=True)
class DollarLine(Line):
    @property
    def prefix(self):
        return "$"

    @property
    @abstractmethod
    def _content_as_is(self) -> Sequence[Token]:
        ...

    @property
    def content(self) -> Sequence[Token]:
        return (ValueToken(" " + self._content_as_is[0].value),)


@attr.s(auto_attribs=True, frozen=True)
class LooseDollarLine(DollarLine):
    text: str = ""

    @property
    def _content_as_is(self):
        return (ValueToken(f"({self.text})"),)


@attr.s(auto_attribs=True, frozen=True)
class ImageDollarLine(DollarLine):
    number: str = ""
    letter: Optional[str] = ""
    text: str = ""

    @property
    def _content_as_is(self):
        return (ValueToken(f'(image {self.number}{self.letter or ""} = {self.text})'),)


@attr.s(auto_attribs=True, frozen=True)
class RulingDollarLine(DollarLine):
    number: atf.Ruling

    @property
    def _content_as_is(self):
        return (ValueToken(f"{self.number.value} ruling"),)


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
                "text can only be initialized if the content is 'object' or 'surface'"
            )

    def to_value_token(self):
        if self.text:
            return f"{self.content.name.lower()} {self.text}"
        else:
            return f"{self.content.name.lower()}"


@attr.s(auto_attribs=True, frozen=True)
class StateDollarLine(DollarLine):
    Range = Tuple[int, int]
    qualification: Optional[atf.Qualification]
    extent: Optional[Union[atf.Extent, int, Range]]
    scope: Optional[ScopeContainer]
    state: Optional[atf.State]
    status: Optional[atf.Status]

    @property
    def _content_as_is(self):
        return (
            ValueToken(
                " ".join(
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
            ),
        )

    @singledispatchmethod
    @staticmethod
    def to_atf(column) -> str:
        return str(column)

    @staticmethod
    @to_atf.register
    def tuple_to_atf(column: tuple) -> str:
        return f"{column[0]}-{column[1]}"

    @staticmethod
    @to_atf.register
    def enum_to_atf(column: Enum) -> str:
        return column.value

    @staticmethod
    @to_atf.register
    def scope_container_to_atf(column: ScopeContainer) -> str:
        return column.to_value_token()
