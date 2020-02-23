from enum import Enum
from functools import singledispatchmethod  # type: ignore
from typing import Optional, Union, Sequence

import attr

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.tokens import ValueToken, Token


@attr.s(auto_attribs=True, frozen=True)
class Seal:
    number: int

    def to_atf(self):
        return "seal " + str(self.number)


@attr.s(auto_attribs=True, frozen=True)
class Heading:
    number: int

    def to_atf(self):
        return "h" + str(self.number)


@attr.s(auto_attribs=True, frozen=True)
class Column:
    number: int

    def to_atf(self):
        return "column " + str(self.number)


@attr.s(auto_attribs=True, frozen=True)
class AtLine(Line):
    structural_tag: Union[atf.Surface, atf.Object, Seal, Column, Heading, atf.Discourse]
    status: Optional[atf.Status]
    text: str = ""

    @property
    def prefix(self):
        return "@"

    @property
    def content(self) -> Sequence[Token]:
        return (
            ValueToken(
                " "
                + " ".join(
                    [
                        AtLine.to_atf(x)
                        for x in [self.structural_tag, self.text, self.status,]
                        if x
                    ]
                )
            ),
        )

    @singledispatchmethod
    @staticmethod
    def to_atf(structural_tag):
        return structural_tag.to_atf()

    @to_atf.register(str)
    @staticmethod
    def text_to_atf(text: str):
        return text

    @to_atf.register(Enum)
    @staticmethod
    def enum_to_atf(structural_tag: Enum):
        return structural_tag.value

    @to_atf.register(atf.Surface)
    @staticmethod
    def surface_to_atf(structural_tag: atf.Surface):
        return structural_tag.value[0]
