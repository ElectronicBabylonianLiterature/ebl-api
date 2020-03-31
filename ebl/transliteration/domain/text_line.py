from typing import Callable, Iterable, Optional, Sequence, Type, TypeVar

import attr
import pydash

from ebl.merger import Merger
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.atf_visitor import AtfVisitor
from ebl.transliteration.domain.enclosure_visitor import EnclosureUpdater
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.language_visitor import LanguageVisitor
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.tokens import Token


L = TypeVar("L", "TextLine", "Line")
T = TypeVar("T")


@attr.s(auto_attribs=True, frozen=True)
class TextLine(Line):
    _prefix: str = ""
    _content: Sequence[Token] = tuple()
    line_number: Optional[AbstractLineNumber] = None

    @property
    def key(self) -> str:
        tokens = "⁚".join(token.get_key() for token in self.content)
        line_number = self.line_number.atf if self.line_number else "None"
        return f"{type(self).__name__}⁞{line_number}⁞{self.atf}⟨{tokens}⟩"

    @property
    def prefix(self):
        return self._prefix

    @property
    def content(self):
        return self._content

    @classmethod
    def of_iterable(cls, line_number: AbstractLineNumber, content: Iterable[Token]):
        enclosure_visitor = EnclosureUpdater()
        for token in content:
            token.accept(enclosure_visitor)

        language_visitor = LanguageVisitor()
        for token in enclosure_visitor.tokens:
            token.accept(language_visitor)

        return cls(line_number.atf, language_visitor.tokens, line_number)

    @classmethod
    def of_legacy_iterable(
        cls,
        line_number_label: LineNumberLabel,
        content: Iterable[Token],
        line_number: Optional[AbstractLineNumber] = None,
    ):
        enclosure_visitor = EnclosureUpdater()
        for token in content:
            token.accept(enclosure_visitor)

        language_visitor = LanguageVisitor()
        for token in enclosure_visitor.tokens:
            token.accept(language_visitor)

        return cls(line_number_label.to_atf(), language_visitor.tokens, line_number)

    @property
    def line_number_label(self) -> LineNumberLabel:
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
            TextLine.of_legacy_iterable(
                other.line_number_label, merge_tokens(), other.line_number
            )
            if isinstance(other, TextLine)
            else other
        )

    def strip_alignments(self) -> "TextLine":
        stripped_content = tuple(token.strip_alignment() for token in self.content)
        return attr.evolve(self, content=stripped_content)
