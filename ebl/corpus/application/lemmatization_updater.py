from typing import Sequence

import attr

from ebl.corpus.application.lemmatization import (
    ChapterLemmatization,
    LineLemmatization,
    LineVariantLemmatization,
)
from ebl.corpus.application.line_updater import (
    EachLineUpdater,
    LineUpdater,
    require_count,
    require_manuscript_token_counts,
)
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.lemmatization.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.text_line import update_tokens
from ebl.transliteration.domain.tokens import Token

MISSING_VARIANT = LineVariantLemmatization((), ())


def _set_unique_lemma(token: Token, lemma: LemmatizationToken) -> Token:
    return token.set_unique_lemma(lemma)


@attr.s(auto_attribs=True, frozen=True)
class _VariantLemmatizer:
    lemmatization: LineVariantLemmatization
    position: str

    def lemmatize(self, variant: LineVariant) -> LineVariant:
        manuscripts = tuple(
            self._lemmatize_manuscript_line(index, manuscript_line)
            for index, manuscript_line in enumerate(variant.manuscripts)
        )
        if len(self.lemmatization.manuscripts) != len(variant.manuscripts):
            raise LemmatizationError()
        return attr.evolve(
            variant,
            reconstruction=update_tokens(
                variant.reconstruction,
                self.lemmatization.reconstruction,
                _set_unique_lemma,
                LemmatizationError,
            ),
            manuscripts=manuscripts,
        )

    def _lemmatize_manuscript_line(
        self, index: int, manuscript_line: ManuscriptLine
    ) -> ManuscriptLine:
        if index >= len(self.lemmatization.manuscripts):
            raise LemmatizationError(
                f"No lemmatization for {self.position} manuscript {index}."
            )
        return attr.evolve(
            manuscript_line,
            line=manuscript_line.line.update_lemmatization(
                self.lemmatization.manuscripts[index]
            ),
        )


def _find_variant(
    variants: Sequence[LineVariantLemmatization], index: int
) -> LineVariantLemmatization:
    return variants[index] if index < len(variants) else MISSING_VARIANT


def lemmatize_line(line: Line, lemmatization: LineLemmatization) -> Line:
    variants = tuple(
        _VariantLemmatizer(
            _find_variant(lemmatization.variants, index),
            f"line {lemmatization.index} variant {index}",
        ).lemmatize(variant)
        for index, variant in enumerate(line.variants)
    )
    if len(lemmatization.variants) != len(line.variants):
        raise LemmatizationError()
    return attr.evolve(line, variants=variants)


class LemmatizationUpdater(EachLineUpdater):
    def __init__(self, lemmatization: ChapterLemmatization) -> None:
        super().__init__()
        self._lemmatization = lemmatization

    def _validate_chapter(self, chapter: Chapter) -> None:
        if len(self._lemmatization) != len(chapter.lines):
            raise LemmatizationError()

    def _update_line(self, index: int, line: Line) -> Line:
        return lemmatize_line(
            line, LineLemmatization(index, self._lemmatization[index])
        )


class LineLemmatizationUpdater(LineUpdater):
    def __init__(self, lemmatization: LineLemmatization) -> None:
        super().__init__(lemmatization.index)
        self._lemmatization = lemmatization

    def _update_line(self, line: Line) -> Line:
        variants = self._lemmatization.variants
        require_manuscript_token_counts(
            LemmatizationError,
            line,
            [
                [len(manuscript) for manuscript in variant.manuscripts]
                for variant in variants
            ],
        )
        for index, variant in enumerate(line.variants):
            require_count(
                LemmatizationError,
                f"reconstruction tokens in variant {index}",
                len(variants[index].reconstruction),
                len(variant.reconstruction),
            )
        return lemmatize_line(line, self._lemmatization)
