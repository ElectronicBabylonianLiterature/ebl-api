# pylint: disable=R0903
from typing import Tuple, NewType, Iterable
import attr
from ebl.fragmentarium.language import Language


UniqueLemma = NewType('UniqueLemma', str)


@attr.s(auto_attribs=True, frozen=True)
class Token:
    value: str

    @property
    def lemmatizable(self) -> bool:
        return False


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


@attr.s(auto_attribs=True, frozen=True)
class Line:
    prefix: str = ''
    content: Tuple[Token, ...] = tuple()

    @classmethod
    def of_iterable(cls, prefix: str, content: Iterable[Token]):
        return cls(prefix, tuple(content))

    @classmethod
    def of_single(cls, prefix: str, content: Token):
        return cls(prefix, (content, ))


@attr.s(auto_attribs=True, frozen=True)
class ControlLine(Line):
    pass


@attr.s(auto_attribs=True, frozen=True)
class TextLine(Line):
    pass


@attr.s(auto_attribs=True, frozen=True)
class EmptyLine(Line):
    pass
