from typing import Sequence, Tuple

import attr

from ebl.corpus.application.line_updater import EachLineUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.word_instances import (
    WordLemma,
    find_word_instances,
    is_word_instance,
)
from ebl.errors import DataError
from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Token

NO_WORD_INSTANCE = 'The chapter has no instance of the word "{}". Nothing was saved.'
NO_LEMMA_CHANGE = (
    'Every instance of the word "{}" already has the lemma {}. Nothing was saved.'
)


class WordInstancesLemmatizer(EachLineUpdater):
    def __init__(self, word_lemma: WordLemma) -> None:
        super().__init__()
        self._word_lemma = word_lemma

    @property
    def _word(self) -> str:
        return self._word_lemma.word

    def _validate_chapter(self, chapter: Chapter) -> None:
        instances = [
            instance
            for line in chapter.lines
            for instance in find_word_instances(line, self._word)
        ]
        if not instances:
            raise DataError(NO_WORD_INSTANCE.format(self._word))
        if all(map(self._word_lemma.is_lemma_of, instances)):
            raise DataError(
                NO_LEMMA_CHANGE.format(
                    self._word, ", ".join(self._word_lemma.unique_lemma)
                )
            )

    def _update_line(self, index: int, line: Line) -> Line:
        return (
            attr.evolve(
                line, variants=tuple(map(self._lemmatize_variant, line.variants))
            )
            if find_word_instances(line, self._word)
            else line
        )

    def _lemmatize_variant(self, variant: LineVariant) -> LineVariant:
        return attr.evolve(
            variant,
            reconstruction=self._lemmatize_tokens(variant.reconstruction),
            manuscripts=tuple(
                map(self._lemmatize_manuscript_line, variant.manuscripts)
            ),
        )

    def _lemmatize_manuscript_line(
        self, manuscript_line: ManuscriptLine
    ) -> ManuscriptLine:
        line = manuscript_line.line
        return (
            attr.evolve(
                manuscript_line,
                line=attr.evolve(line, content=self._lemmatize_tokens(line.content)),
            )
            if isinstance(line, TextLine)
            else manuscript_line
        )

    def _lemmatize_tokens(self, tokens: Sequence[Token]) -> Tuple[Token, ...]:
        return tuple(map(self._lemmatize_token, tokens))

    def _lemmatize_token(self, token: Token) -> Token:
        return (
            token.set_unique_lemma(
                LemmatizationToken(token.value, self._word_lemma.unique_lemma)
            )
            if is_word_instance(token, self._word)
            else token
        )
