from abc import ABC, abstractmethod
from enum import Enum
from functools import singledispatchmethod  # type: ignore
from typing import Callable, Iterable, Sequence, Tuple, Type, TypeVar, Optional, Union

import attr
import pydash

import ebl.transliteration.domain.atf as atf
from ebl.merger import Merger
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.atf import Atf, WORD_SEPARATOR
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.tokens import Token, ValueToken
from ebl.transliteration.domain.visitors import AtfVisitor, LanguageVisitor

T = TypeVar("T")
L = TypeVar("L", "TextLine", "Line")


@attr.s(auto_attribs=True, frozen=True)
class Line(ABC):
    @property
    @abstractmethod
    def prefix(self) -> str:
        ...

    @property
    @abstractmethod
    def content(self) -> Sequence[Token, ...]:
        ...

    @property
    def key(self) -> str:
        tokens = [token.get_key() for token in self.content]
        return "⁞".join([str(self.atf)] + tokens)

    @property
    def atf(self) -> Atf:
        content = WORD_SEPARATOR.join(token.value for token in self.content)
        return Atf(f"{self.prefix}{content}")

    def update_lemmatization(
        self, lemmatization: Sequence[LemmatizationToken]
    ) -> "Line":
        def updater(token, lemmatization_token):
            return token.set_unique_lemma(lemmatization_token)

        return self._update_tokens(lemmatization, updater, LemmatizationError)

    def update_alignment(self, alignment: Sequence[AlignmentToken]) -> "Line":
        return self

    def _update_tokens(
        self,
        updates: Sequence[T],
        updater: Callable[[Token, T], Token],
        error_class: Type[Exception],
    ) -> "Line":
        return self

    def merge(self, other: "Line") -> "Line":
        return other

    def strip_alignments(self):
        return self


@attr.s(auto_attribs=True, frozen=True)
class ControlLine(Line):
    _prefix: str = ""
    _content: Sequence[Token] = tuple()

    @classmethod
    def of_single(cls, prefix: str, content: Token):
        return cls(prefix, (content,))

    @property
    def prefix(self):
        return self._prefix

    @property
    def content(self):
        return self._content


@attr.s(auto_attribs=True, frozen=True)
class DollarLine(Line):
    @property
    def prefix(self):
        return "$"

    # content = ValueToken(" " + ...) # Contents ValueToken has to start with empty
    # space, so Line.atf() works


@attr.s(auto_attribs=True, frozen=True)
class LooseDollarLine(DollarLine):
    text: str = ""

    @property
    def content(self):
        return (ValueToken(f" ({self.text})"),)


@attr.s(auto_attribs=True, frozen=True)
class ImageDollarLine(DollarLine):
    number: str = ""
    letter: Optional[str] = ""
    text: str = ""

    @property
    def content(self):
        return (ValueToken(f' (image {self.number}{self.letter or ""} = {self.text})'),)


@attr.s(auto_attribs=True, frozen=True)
class RulingDollarLine(DollarLine):
    number: atf.Ruling

    @property
    def content(self):
        return (ValueToken(f" {self.number.value} ruling"),)


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

    def __str__(self):
        if self.text:
            return f"{self.content.name.lower()} {self.text}"
        else:
            return f"{self.content.name.lower()}"


Range = Tuple[int, int]


@attr.s(auto_attribs=True, frozen=True)
class StrictDollarLine(DollarLine):
    qualification: Optional[atf.Qualification]
    extent: Union[atf.Extent, int, Range]
    scope: ScopeContainer
    state: Optional[atf.State]
    status: Optional[atf.Status]

    @property
    def content(self):
        return (
            ValueToken(
                " "
                + " ".join(
                    [
                        StrictDollarLine.to_atf(x)
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
    def to_atf(val):
        return str(val)

    @to_atf.register(tuple)
    @staticmethod
    def tuple_to_atf(val: tuple):
        return f"{val[0]}-{val[1]}"

    @to_atf.register(Enum)
    @staticmethod
    def enum_to_atf(val: Enum):
        return val.value


@attr.s(auto_attribs=True, frozen=True)
class TextLine(Line):
    _prefix: str = ""
    _content: Sequence[Token] = tuple()

    @property
    def prefix(self):
        return self._prefix

    @property
    def content(self):
        return self._content

    @classmethod
    def of_iterable(cls, line_number: LineNumberLabel, content: Iterable[Token]):
        visitor = LanguageVisitor()
        for token in content:
            token.accept(visitor)
        return cls(line_number.to_atf(), visitor.tokens)

    @property
    def line_number(self) -> LineNumberLabel:
        return LineNumberLabel.from_atf(self.prefix)

    @property
    def atf(self) -> Atf:
        visitor = AtfVisitor(self.prefix)
        for token in self.content:
            token.accept(visitor)
        return visitor.result

    def update_alignment(self, alignment: Sequence[AlignmentToken]) -> "Line":
        def updater(token, alignment_token):
            return token.set_alignment(alignment_token)

        return self._update_tokens(alignment, updater, AlignmentError)

    def _update_tokens(
        self,
        updates: Sequence[T],
        updater: Callable[[Token, T], Token],
        error_class: Type[Exception],
    ) -> "Line":
        if len(self.content) == len(updates):
            zipped = pydash.zip_(list(self.content), list(updates))
            content = tuple(updater(pair[0], pair[1]) for pair in zipped)
            return attr.evolve(self, content=content)
        else:
            raise error_class()

    def merge(self, other: L) -> L:
        def merge_tokens():
            def map_(token):
                return token.get_key()

            def inner_merge(old: Token, new: Token) -> Token:
                return old.merge(new)

            return Merger(map_, inner_merge).merge(self.content, other.content)

        return (
            TextLine.of_iterable(other.line_number, merge_tokens())
            if isinstance(other, TextLine)
            else other
        )

    def strip_alignments(self) -> "TextLine":
        stripped_content = tuple(token.strip_alignment() for token in self.content)
        return attr.evolve(self, content=stripped_content)


@attr.s(auto_attribs=True, frozen=True)
class EmptyLine(Line):
    @property
    def prefix(self):
        return ""

    @property
    def content(self):
        return tuple()
