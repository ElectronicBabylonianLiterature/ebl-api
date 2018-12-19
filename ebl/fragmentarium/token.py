from typing import Any, Tuple, NewType
import attr
from ebl.fragmentarium.language import Language, DEFAULT_LANGUAGE


DEFAULT_LANGUAGE = Language.AKKADIAN
DEFAULT_NORMALIZED = False
UniqueLemma = NewType('UniqueLemma', str)


@attr.s(auto_attribs=True, frozen=True)
class Token:
    value: str

    @property
    def lemmatizable(self) -> bool:
        return False

    def accept(self, visitor: Any) -> None:
        visitor.visit_token(self)


@attr.s(auto_attribs=True, frozen=True)
class Word(Token):
    language: Language = DEFAULT_LANGUAGE
    normalized: bool = DEFAULT_NORMALIZED
    unique_lemma: Tuple[UniqueLemma, ...] = tuple()

    @property
    def lemmatizable(self) -> bool:
        return self.language.lemmatizable and not self.normalized

    def set_language(self, language: Language, normalized: bool) -> 'Word':
        return attr.evolve(self, language=language, normalized=normalized)

    def accept(self, visitor: Any) -> None:
        visitor.visit_word(self)


@attr.s(auto_attribs=True, frozen=True)
class LanguageShift(Token):
    _normalization_shift = '%n'

    @property
    def language(self):
        return Language.of_atf(self.value)

    @property
    def normalized(self):
        return self.value == LanguageShift._normalization_shift

    def accept(self, visitor: Any) -> None:
        visitor.visit_language_shift(self)
