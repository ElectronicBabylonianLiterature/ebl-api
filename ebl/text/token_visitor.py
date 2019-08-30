from abc import ABC, abstractmethod
from typing import Union

from ebl.text.token import BrokenAway, DocumentOrientedGloss, Erasure, \
    LanguageShift, OmissionOrRemoval, PerhapsBrokenAway, Token
from ebl.text.word import Word


class TokenVisitor(ABC):
    @abstractmethod
    def visit_token(self, token: Token) -> None:
        ...

    @abstractmethod
    def visit_language_shift(self, shift: LanguageShift) -> None:
        ...

    @abstractmethod
    def visit_word(self, word: Word) -> None:
        ...

    @abstractmethod
    def visit_document_oriented_gloss(
            self, gloss: DocumentOrientedGloss
    ) -> None:
        ...

    @abstractmethod
    def visit_broken_away(
            self, broken_away: Union[BrokenAway, PerhapsBrokenAway]
    ) -> None:
        ...

    @abstractmethod
    def visit_omission_or_removal(
            self, omission: OmissionOrRemoval
    ) -> None:
        ...

    @abstractmethod
    def visit_erasure(self, erasure: Erasure):
        ...
