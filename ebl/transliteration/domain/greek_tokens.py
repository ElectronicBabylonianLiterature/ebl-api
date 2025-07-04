from typing import Optional, Sequence

import attr

import ebl.transliteration.domain.atf as atf
from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.transliteration.domain.converters import convert_flag_sequence
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.tokens import ErasureState, Token, TokenVisitor
from ebl.transliteration.domain.word_tokens import AbstractWord

GREEK_LETTERS: str = "ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω"


@attr.s(auto_attribs=True, frozen=True)
class GreekLetter(Token):
    letter: str = attr.ib(validator=attr.validators.in_(GREEK_LETTERS))
    flags: Sequence[atf.Flag] = attr.ib(converter=convert_flag_sequence)

    @property
    def value(self) -> str:
        flags = "".join(flag.value for flag in self.flags)
        return f"{self.letter}{flags}"

    @property
    def clean_value(self) -> str:
        return self.letter

    @property
    def parts(self):
        return ()

    @staticmethod
    def of(letter: str, flags: Sequence[atf.Flag] = ()):
        return GreekLetter(frozenset(), ErasureState.NONE, letter, flags)


@attr.s(auto_attribs=True, frozen=True, str=False)
class GreekWord(AbstractWord):
    _language: Language = Language.GREEK

    @property
    def language(self) -> Language:
        return self._language

    @property
    def normalized(self) -> bool:
        return False

    @property
    def alignable(self) -> bool:
        return self.lemmatizable or self.language == Language.SUMERIAN

    @property
    def value(self) -> str:
        return "".join(part.value for part in self.parts)

    def set_language(self, language: Language) -> "GreekWord":
        return attr.evolve(self, language=language)

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_greek_word(self)

    @staticmethod
    def of(
        parts: Sequence[Token],
        language: Language = Language.GREEK,
        unique_lemma: Lemma = (),
        alignment: Optional[int] = None,
        variant: Optional[AbstractWord] = None,
        erasure: ErasureState = ErasureState.NONE,
        has_variant_alignment: bool = False,
        has_omitted_alignment: bool = False,
        id_: Optional[str] = None,
    ) -> "GreekWord":
        return GreekWord(
            frozenset(),
            erasure,
            id_,
            unique_lemma,
            alignment,
            parts,
            variant,
            has_variant_alignment,
            has_omitted_alignment,
            language,
        )
