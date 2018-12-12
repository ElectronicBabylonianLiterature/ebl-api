from typing import Any, Tuple, NewType
from ebl.fragmentarium.language import Language


class Token():
    def __init__(self, value: str) -> None:
        self.__value = value

    @property
    def value(self) -> str:
        return self.__value

    @property
    def lemmatizable(self) -> bool:
        return False

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Token) and (self.value == other.value)

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f'{type(self).__name__}("{self.value}")'

    def __str__(self) -> str:
        return self.value


UniqueLemma = NewType('UniqueLemma', str)


class Word(Token):
    def __init__(
            self,
            value: str,
            language: Language,
            unique_lemma: Tuple[UniqueLemma, ...] = tuple()
    ) -> None:
        super().__init__(value)
        self.__language = language
        self.__unique_lemma = unique_lemma

    @property
    def language(self) -> Language:
        return self.__language

    @property
    def unique_lemma(self) -> Tuple[UniqueLemma, ...]:
        return self.__unique_lemma

    @property
    def lemmatizable(self) -> bool:
        return self.language.lemmatizable

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, Word) and
            self.value == other.value and
            self.language == other.language and
            self.unique_lemma == other.unique_lemma
        )

    def __hash__(self) -> int:
        return hash((self.value, self.language, self.unique_lemma))

    def __repr__(self) -> str:
        properties =\
            f'"{self.value}", "{self.language}", "{self.unique_lemma}"'
        return f'{type(self).__name__}({properties})'
