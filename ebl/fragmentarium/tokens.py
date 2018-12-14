# pylint: disable=R0903
from typing import Tuple, NewType
import attr
from ebl.fragmentarium.language import Language


@attr.s(auto_attribs=True, frozen=True)
class Token:
    value: str

    @property
    def lemmatizable(self) -> bool:
        return False


UniqueLemma = NewType('UniqueLemma', str)


@attr.s(auto_attribs=True, frozen=True)
class Word(Token):
    language: Language = Language.AKKADIAN
    unique_lemma: Tuple[UniqueLemma, ...] = tuple()

    @property
    def lemmatizable(self) -> bool:
        return self.language.lemmatizable


@attr.s(auto_attribs=True, frozen=True)
class Shift(Token):
    language: Language = attr.ib(init=False)

    def __attrs_post_init__(self):
        object.__setattr__(self, 'language', Language.of_atf(self.value))
