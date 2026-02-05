from abc import ABC, abstractmethod
from typing import Sequence, Tuple, TypeVar

import attr

from ebl.fragmentarium.domain.token_annotation import LineLemmaAnnotation
from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.alignment import AlignmentToken
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.tokens import TokenVisitor

L = TypeVar("L", bound="Line")


@attr.s(frozen=True)
class Line(ABC):
    @property
    @abstractmethod
    def atf(self) -> Atf: ...

    @property
    @abstractmethod
    def lemmatization(self) -> Sequence[LemmatizationToken]: ...

    @property
    def key(self) -> str:
        return f"{type(self).__name__}⁞{self.atf}⁞{hash(self)}"

    def update_lemmatization(self: L, lemmatization: Sequence[LemmatizationToken]) -> L:
        return self

    def update_lemma_annotation(self: L, line_annotation: LineLemmaAnnotation) -> L:
        return self

    def update_alignment(self: L, alignment: Sequence[AlignmentToken]) -> L:
        return self

    def merge(self, other: L) -> L:
        return other

    def update_alignments(self: L, alignment_map) -> L:
        return self

    def accept(self, visitor: TokenVisitor) -> None:  # noqa: B027
        pass


@attr.s(auto_attribs=True, frozen=True)
class ControlLine(Line):
    prefix: str
    content: str

    @property
    def atf(self) -> Atf:
        return Atf(f"{self.prefix}{self.content}")

    @property
    def lemmatization(self) -> Tuple[LemmatizationToken]:
        return (LemmatizationToken(self.content),)


@attr.s(auto_attribs=True, frozen=True)
class EmptyLine(Line):
    @property
    def atf(self) -> Atf:
        return Atf("")

    @property
    def lemmatization(self) -> Tuple:
        return ()
