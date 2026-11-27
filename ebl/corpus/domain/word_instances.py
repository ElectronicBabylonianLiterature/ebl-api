from typing import Iterator, Sequence, Tuple

import attr

from ebl.corpus.domain.line import Line
from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.word_tokens import AbstractWord


def is_word_instance(token: Token, word: str) -> bool:
    return token.lemmatizable and token.clean_value == word


def _find_token_sequences(line: Line) -> Iterator[Sequence[Token]]:
    for variant in line.variants:
        yield variant.reconstruction
        for manuscript_line in variant.manuscripts:
            yield manuscript_line.get_line_content()


def find_word_instances(line: Line, word: str) -> Sequence[AbstractWord]:
    return [
        token
        for tokens in _find_token_sequences(line)
        for token in tokens
        if isinstance(token, AbstractWord) and is_word_instance(token, word)
    ]


def _to_lemma(unique_lemma: Lemma) -> Lemma:
    return tuple(unique_lemma)


@attr.s(frozen=True, auto_attribs=True)
class WordLemma:
    word: str
    unique_lemma: Lemma = attr.ib(converter=_to_lemma)

    def is_lemma_of(self, word: AbstractWord) -> bool:
        return tuple(word.unique_lemma) == self.unique_lemma


@attr.s(frozen=True, auto_attribs=True)
class WordInstances:
    word: str
    words: int
    lemmatized: int
    lines: Sequence[int]
    revision: str

    @staticmethod
    def of_lines(lines: Sequence[Line], word: str, revision: str) -> "WordInstances":
        instances: Tuple[Sequence[AbstractWord], ...] = tuple(
            find_word_instances(line, word) for line in lines
        )
        return WordInstances(
            word,
            sum(len(line_instances) for line_instances in instances),
            sum(
                1
                for line_instances in instances
                for instance in line_instances
                if instance.unique_lemma
            ),
            tuple(index for index, found in enumerate(instances) if found),
            revision,
        )
