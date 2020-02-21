from typing import Optional, Union, Sequence, NewType

import attr

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.tokens import ValueToken, Token

Seal = NewType("Seal", int)
Column = NewType("Column", int)
Heading = NewType("Heading", int)


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
        return (ValueToken("TODO"),)
