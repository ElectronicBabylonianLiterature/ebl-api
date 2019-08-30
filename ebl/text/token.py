from enum import Enum, auto

import attr

from ebl.corpus.alignment import AlignmentError, AlignmentToken
from ebl.text.language import Language
from ebl.text.lemmatization import LemmatizationError, LemmatizationToken
from ebl.text.token_visitor import TokenVisitor


class Side(Enum):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()


@attr.s(auto_attribs=True, frozen=True)
class Token:
    value: str

    @property
    def lemmatizable(self) -> bool:
        return False

    @property
    def alignable(self) -> bool:
        return self.lemmatizable

    def set_unique_lemma(
            self,
            lemma: LemmatizationToken
    ) -> 'Token':
        if lemma.unique_lemma is None and lemma.value == self.value:
            return self
        else:
            raise LemmatizationError()

    def set_alignment(self, alignment: AlignmentToken):
        if (
                alignment.alignment is None
                and alignment.value == self.value
        ):
            return self
        else:
            raise AlignmentError()

    def strip_alignment(self):
        return self

    def merge(self, token: 'Token') -> 'Token':
        return token

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_token(self)

    def to_dict(self) -> dict:
        return {
            'type': 'Token',
            'value': self.value
        }


@attr.s(frozen=True)
class LanguageShift(Token):
    _normalization_shift = '%n'

    @property
    def language(self):
        return Language.of_atf(self.value)

    @property
    def normalized(self):
        return self.value == LanguageShift._normalization_shift

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_language_shift(self)

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'LanguageShift',
            'normalized': self.normalized,
            'language': self.language.name
        }


@attr.s(frozen=True)
class DocumentOrientedGloss(Token):
    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_document_oriented_gloss(self)

    @property
    def side(self) -> Side:
        return Side.LEFT if self.value == '{(' else Side.RIGHT

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'DocumentOrientedGloss'
        }


@attr.s(frozen=True)
class BrokenAway(Token):
    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_broken_away(self)

    @property
    def side(self) -> Side:
        return Side.LEFT if self.value == '[' else Side.RIGHT

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'BrokenAway'
        }


@attr.s(frozen=True)
class PerhapsBrokenAway(Token):
    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_broken_away(self)

    @property
    def side(self) -> Side:
        return Side.LEFT if self.value == '(' else Side.RIGHT

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'PerhapsBrokenAway'
        }


@attr.s(auto_attribs=True, frozen=True)
class Erasure(Token):
    side: Side

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_erasure(self)

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'Erasure',
            'side': self.side.name
        }


@attr.s(frozen=True)
class OmissionOrRemoval(Token):
    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_omission_or_removal(self)

    @property
    def side(self) -> Side:
        return Side.LEFT if (
                self.value in ['<(', '<', '<<']
        ) else Side.RIGHT

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'OmissionOrRemoval'
        }


@attr.s(frozen=True)
class LineContinuation(Token):
    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'LineContinuation'
        }
