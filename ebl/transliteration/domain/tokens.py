import collections
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, Tuple, Sequence, Iterable

import attr
import pydash

import ebl.transliteration.domain.atf as atf
from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lemmatization import LemmatizationError, \
    LemmatizationToken
from ebl.transliteration.domain.word_cleaner import clean_word

DEFAULT_LANGUAGE = Language.AKKADIAN
DEFAULT_NORMALIZED = False
Partial = collections.namedtuple('Partial', 'start end')


def convert_token_sequence(tokens: Iterable['Token']) -> Tuple['Token', ...]:
    return tuple(tokens)


def convert_flag_sequence(flags: Iterable[atf.Flag]) -> Tuple[atf.Flag, ...]:
    return tuple(flags)


class Side(Enum):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()


class ErasureState(Enum):
    NONE = auto()
    ERASED = auto()
    OVER_ERASED = auto()


class Token(ABC):
    @property
    @abstractmethod
    def value(self) -> str:
        ...

    def to_dict(self) -> dict:
        return {
            'type': 'Token',
            'value': self.value
        }

    @property
    def lemmatizable(self) -> bool:
        return False

    @property
    def alignable(self) -> bool:
        return self.lemmatizable

    @property
    def parts(self) -> Sequence['Token']:
        return tuple()

    def get_key(self, delimiter: str = '⁝') -> str:
        parts = [part.get_key('⁚') for part in self.parts]
        return delimiter.join([type(self).__name__, self.value] + parts)

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

    def accept(self, visitor: 'TokenVisitor') -> None:
        visitor.visit(self)


@attr.s(auto_attribs=True, frozen=True)
class ValueToken(Token):
    _value: str

    @property
    def value(self) -> str:
        return self._value


@attr.s(auto_attribs=True, frozen=True)
class Word(ValueToken):
    language: Language = DEFAULT_LANGUAGE
    normalized: bool = DEFAULT_NORMALIZED
    unique_lemma: Tuple[WordId, ...] = tuple()
    erasure: ErasureState = ErasureState.NONE
    alignment: Optional[int] = None
    _parts: Sequence[Token] = attr.ib(default=tuple(),
                                      kw_only=True,
                                      converter=convert_token_sequence)

    @property
    def lemmatizable(self) -> bool:
        non_lemmatizables = [
            atf.VARIANT_SEPARATOR,
            atf.UNCLEAR_SIGN,
            atf.UNIDENTIFIED_SIGN,
            atf.UNKNOWN_NUMBER_OF_SIGNS
        ]
        return (
                self.language.lemmatizable and
                not self.normalized and
                self.erasure is not ErasureState.ERASED and
                all((substring not in self.value)
                    for substring
                    in non_lemmatizables) and
                not any(self.partial)
        )

    @property
    def parts(self) -> Sequence[Token]:
        return self._parts

    @property
    def partial(self) -> Partial:
        partials = [*atf.JOINERS, atf.UNKNOWN_NUMBER_OF_SIGNS]
        return Partial(
            any(
                self.value.startswith(partial)
                for partial
                in partials
            ),
            any(
                self.value.endswith(partial)
                for partial
                in partials
            )
        )

    def set_language(self, language: Language, normalized: bool) -> 'Word':
        return attr.evolve(self, language=language, normalized=normalized)

    def set_erasure(self, erasure: ErasureState, ) -> 'Word':
        return attr.evolve(self, erasure=erasure)

    def set_unique_lemma(
            self,
            lemma: LemmatizationToken
    ) -> 'Word':
        value_is_compatible = self.value == lemma.value
        lemma_is_compatible = self.lemmatizable or not lemma.unique_lemma
        if value_is_compatible and lemma_is_compatible:
            return attr.evolve(self,
                               unique_lemma=lemma.unique_lemma or tuple())
        else:
            raise LemmatizationError(f'Cannot apply {lemma} to {self}.')

    def set_alignment(self, alignment: AlignmentToken):
        if (
                self.value == alignment.value
                and (self.alignable or alignment.alignment is None)
        ):
            return attr.evolve(
                self,
                alignment=alignment.alignment
            )
        else:
            raise AlignmentError()

    def strip_alignment(self):
        return attr.evolve(self, alignment=None)

    def merge(self, token: Token) -> Token:
        same_value = clean_word(self.value) == clean_word(token.value)
        is_compatible = type(token) == Word and same_value

        result = token
        if is_compatible and token.lemmatizable:
            result = result.set_unique_lemma(
                LemmatizationToken(token.value, self.unique_lemma)
            )
        if is_compatible and token.alignable:
            result = result.set_alignment(
                AlignmentToken(token.value, self.alignment)
            )
        return result

    def to_dict(self) -> dict:
        return pydash.omit_by({
            **super().to_dict(),
            'type': 'Word',
            'uniqueLemma': [*self.unique_lemma],
            'normalized': self.normalized,
            'language': self.language.name,
            'lemmatizable': self.lemmatizable,
            'erasure': self.erasure.name,
            'alignment': self.alignment,
            'parts': [token.to_dict() for token in self.parts]
        }, lambda value: value is None)


@attr.s(auto_attribs=True, frozen=True)
class LoneDeterminative(Word):
    _partial: Partial = attr.ib(default=Partial(False, False), kw_only=True)

    @staticmethod
    def of_value(value: str,
                 partial: Partial,
                 erasure: ErasureState = ErasureState.NONE,
                 parts=tuple()) -> 'LoneDeterminative':
        return LoneDeterminative(value,
                                 erasure=erasure,
                                 partial=partial,
                                 parts=parts)

    @property
    def lemmatizable(self) -> bool:
        return False

    @property
    def partial(self) -> Partial:
        return self._partial

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'LoneDeterminative',
            'partial': list(self.partial)
        }


@attr.s(frozen=True)
class LanguageShift(ValueToken):
    _normalization_shift = '%n'

    @property
    def language(self):
        return Language.of_atf(self.value)

    @property
    def normalized(self):
        return self.value == LanguageShift._normalization_shift

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'LanguageShift',
            'normalized': self.normalized,
            'language': self.language.name
        }


@attr.s(frozen=True)
class DocumentOrientedGloss(ValueToken):
    @property
    def side(self) -> Side:
        return Side.LEFT if self.value == '{(' else Side.RIGHT

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'DocumentOrientedGloss'
        }


@attr.s(frozen=True)
class BrokenAway(ValueToken):
    @property
    def side(self) -> Side:
        return Side.LEFT if self.value == '[' else Side.RIGHT

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'BrokenAway'
        }


@attr.s(frozen=True)
class PerhapsBrokenAway(ValueToken):
    @property
    def side(self) -> Side:
        return Side.LEFT if self.value == '(' else Side.RIGHT

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'PerhapsBrokenAway'
        }


@attr.s(auto_attribs=True, frozen=True)
class Erasure(ValueToken):
    side: Side

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'Erasure',
            'side': self.side.name
        }


@attr.s(frozen=True)
class OmissionOrRemoval(ValueToken):
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
class UnknownNumberOfSigns(Token):
    @property
    def value(self) -> str:
        return atf.UNKNOWN_NUMBER_OF_SIGNS

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'UnknownNumberOfSigns'
        }


@attr.s(frozen=True)
class Tabulation(ValueToken):
    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'Tabulation'
        }


@attr.s(frozen=True)
class CommentaryProtocol(ValueToken):
    @property
    def protocol(self):
        return atf.CommentaryProtocol(self.value)

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'CommentaryProtocol'
        }


@attr.s(frozen=True, auto_attribs=True)
class Divider(Token):
    divider: str
    modifiers: Tuple[str, ...] = tuple()
    flags: Tuple[atf.Flag, ...] = tuple()

    @property
    def value(self) -> str:
        modifiers = ''.join(self.modifiers)
        flags = ''.join(self.string_flags)
        return f'{self.divider}{modifiers}{flags}'

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'Divider',
            'divider': self.divider,
            'modifiers': list(self.modifiers),
            'flags': self.string_flags
        }


@attr.s(frozen=True, auto_attribs=True)
class Column(Token):
    number: Optional[int] = attr.ib(default=None)

    @number.validator
    def _check_number(self, _, value) -> None:
        if value is not None and value < 0:
            raise ValueError("number must not be negative")

    @property
    def value(self) -> str:
        return '&' if self.number is None else f'&{self.number}'

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'Column',
            'number': self.number
        }


@attr.s(frozen=True, auto_attribs=True)
class Variant(Token):
    tokens: Tuple[Token, ...]

    @staticmethod
    def of(first: Token, second: Token) -> 'Variant':
        return Variant((first, second))

    @property
    def value(self) -> str:
        return '/'.join(token.value for token in self.tokens)

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'Variant',
            'tokens': [token.to_dict() for token in self.tokens]
        }


@attr.s(frozen=True)
class Joiner(ValueToken):
    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'Joiner'
        }


@attr.s(auto_attribs=True, frozen=True)
class AbstractSign(Token):
    flags: Sequence[atf.Flag] = attr.ib(default=tuple(),
                                        converter=convert_flag_sequence)

    @property
    @abstractmethod
    def _sign(self) -> str:
        ...

    @property
    @abstractmethod
    def _type(self) -> str:
        ...

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]

    @property
    def value(self) -> str:
        return f'{self._sign}{"".join(self.string_flags)}'

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': self._type,
            'flags': list(self.string_flags)
        }


@attr.s(auto_attribs=True, frozen=True)
class UnidentifiedSign(AbstractSign):
    @property
    def _sign(self) -> str:
        return atf.UNIDENTIFIED_SIGN

    @property
    def _type(self) -> str:
        return 'UnidentifiedSign'


@attr.s(auto_attribs=True, frozen=True)
class UnclearSign(AbstractSign):
    @property
    def _sign(self) -> str:
        return atf.UNCLEAR_SIGN

    @property
    def _type(self) -> str:
        return 'UnclearSign'


@attr.s(frozen=True)
class LineContinuation(ValueToken):
    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'LineContinuation'
        }


class TokenVisitor(ABC):
    @abstractmethod
    def visit(self, token: Token) -> None:
        ...
