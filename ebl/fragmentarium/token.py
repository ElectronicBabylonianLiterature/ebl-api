from typing import Any, Tuple, NewType
import attr
from ebl.fragmentarium.language import Language, DEFAULT_LANGUAGE


DEFAULT_LANGUAGE = Language.AKKADIAN
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
    unique_lemma: Tuple[UniqueLemma, ...] = tuple()

    @property
    def lemmatizable(self) -> bool:
        return self.language.lemmatizable

    def set_language(self, language: Language) -> 'Word':
        return attr.evolve(self, language=language)

    def accept(self, visitor: Any) -> None:
        visitor.visit_word(self)


@attr.s(auto_attribs=True, frozen=True)
class LanguageShift(Token):
    language: Language = attr.ib(init=False)

    def __attrs_post_init__(self):
        object.__setattr__(self, 'language', Language.of_atf(self.value))

    def accept(self, visitor: Any) -> None:
        visitor.visit_language_shift(self)
