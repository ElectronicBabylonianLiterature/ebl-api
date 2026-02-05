from abc import abstractmethod
from typing import Optional, Sequence, Type, TypeVar

import attr
import pydash

from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import Enclosure
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.tokens import ErasureState, Token, TokenVisitor
from ebl.transliteration.domain.word_tokens import AbstractWord


@attr.s(auto_attribs=True, frozen=True, str=False)
class AkkadianWord(AbstractWord):
    modifiers: Sequence[Flag] = attr.ib(default=())

    @modifiers.validator
    def _validate_modifiers(self, _, value):
        allowed_modifiers = set(Flag) - {Flag.COLLATION}
        if not set(value).issubset(allowed_modifiers):
            raise ValueError(f"Invalid modifiers: {value}")

    @property
    def language(self) -> Language:
        return Language.AKKADIAN

    @property
    def normalized(self) -> bool:
        return True

    @property
    def value(self) -> str:
        last_parts = pydash.take_right_while(
            self.parts, lambda part: isinstance(part, Enclosure)
        )
        main_parts = self.parts[: len(self.parts) - len(last_parts)]
        return "".join(
            [part.value for part in main_parts]
            + [modifier.value for modifier in self.modifiers]
            + [part.value for part in last_parts]
        )

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_akkadian_word(self)

    @staticmethod
    def of(
        parts: Sequence[Token],
        modifier: Sequence[Flag] = (),
        unique_lemma: Lemma = (),
        alignment: Optional[int] = None,
        variant: Optional[AbstractWord] = None,
        has_variant_alignment: bool = False,
        has_omitted_alignment: bool = False,
        id_: Optional[str] = None,
        named_entities: Sequence[str] = (),
    ) -> "AkkadianWord":
        return AkkadianWord(
            frozenset(),
            ErasureState.NONE,
            id_,
            unique_lemma,
            alignment,
            parts,
            variant,
            has_variant_alignment,
            has_omitted_alignment,
            named_entities,
            modifier,
        )


B = TypeVar("B", bound="Break")


@attr.s(auto_attribs=True, frozen=True, str=False)
class Break(Token):
    is_uncertain: bool

    @property
    @abstractmethod
    def _symbol(self) -> str: ...

    @property
    def parts(self) -> Sequence["Token"]:
        return ()

    @property
    def value(self) -> str:
        return f"({self._symbol})" if self.is_uncertain else self._symbol

    @classmethod
    def of(cls: Type[B], is_uncertain: bool) -> B:
        return cls(frozenset(), ErasureState.NONE, is_uncertain)

    @classmethod
    def certain(cls: Type[B]) -> B:
        return cls(frozenset(), ErasureState.NONE, False)

    @classmethod
    def uncertain(cls: Type[B]) -> B:
        return cls(frozenset(), ErasureState.NONE, True)


@attr.s(frozen=True, str=False)
class Caesura(Break):
    @property
    def _symbol(self) -> str:
        return "||"

    def accept(self, visitor: TokenVisitor):
        visitor.visit_caesura(self)


@attr.s(frozen=True, str=False)
class MetricalFootSeparator(Break):
    @property
    def _symbol(self) -> str:
        return "|"

    def accept(self, visitor: TokenVisitor):
        visitor.visit_metrical_foot_separator(self)
