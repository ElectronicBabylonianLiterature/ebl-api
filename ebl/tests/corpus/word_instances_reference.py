from functools import reduce
from typing import Callable, List, Sequence, Tuple, Union

import attr

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.application.lemmatization import LineVariantLemmatization
from ebl.lemmatization.domain.lemmatization import Lemma, LemmatizationToken
from ebl.tests.corpus.line_annotation_support import replace_item
from ebl.tests.corpus.word_instances_support import (
    MANUSCRIPT_INSTANCES,
    NEW_LEMMA,
    RECONSTRUCTION_INSTANCES,
    ManuscriptPosition,
    ReconstructionPosition,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.word_tokens import AbstractWord

VariantChange = Callable[[LineVariant], LineVariant]
TokenPath = List[Union[int, str]]


def find_reconstruction_token(
    chapter: Chapter, instance: ReconstructionPosition
) -> Token:
    variant = chapter.lines[instance.line].variants[instance.variant]
    return variant.reconstruction[instance.token]


def _find_manuscript_line(
    variant: LineVariant, instance: ManuscriptPosition
) -> ManuscriptLine:
    return variant.manuscripts[instance.manuscript]


def find_manuscript_token(chapter: Chapter, instance: ManuscriptPosition) -> Token:
    variant = chapter.lines[instance.line].variants[instance.variant]
    return _find_manuscript_line(variant, instance).get_line_content()[instance.token]


def _set_lemma(tokens: Sequence[Token], index: int, lemma: Lemma) -> Tuple[Token, ...]:
    word = tokens[index]
    assert isinstance(word, AbstractWord)
    return replace_item(tokens, index, attr.evolve(word, unique_lemma=lemma))


def _change_variant(
    chapter: Chapter, line_index: int, variant_index: int, change: VariantChange
) -> Chapter:
    line = chapter.lines[line_index]
    variants = replace_item(
        line.variants, variant_index, change(line.variants[variant_index])
    )
    return attr.evolve(
        chapter,
        lines=replace_item(
            chapter.lines, line_index, attr.evolve(line, variants=variants)
        ),
    )


def _lemmatize_reconstruction(
    lemma: Lemma, chapter: Chapter, instance: ReconstructionPosition
) -> Chapter:
    def change(variant: LineVariant) -> LineVariant:
        return attr.evolve(
            variant,
            reconstruction=_set_lemma(variant.reconstruction, instance.token, lemma),
        )

    return _change_variant(chapter, instance.line, instance.variant, change)


def _lemmatize_manuscript(
    lemma: Lemma, chapter: Chapter, instance: ManuscriptPosition
) -> Chapter:
    def change(variant: LineVariant) -> LineVariant:
        manuscript_line = _find_manuscript_line(variant, instance)
        text_line = manuscript_line.line
        assert isinstance(text_line, TextLine)
        content = _set_lemma(text_line.content, instance.token, lemma)
        return attr.evolve(
            variant,
            manuscripts=replace_item(
                variant.manuscripts,
                instance.manuscript,
                attr.evolve(
                    manuscript_line, line=attr.evolve(text_line, content=content)
                ),
            ),
        )

    return _change_variant(chapter, instance.line, instance.variant, change)


def lemmatize_instances(chapter: Chapter, lemma: Lemma = NEW_LEMMA) -> Chapter:
    def lemmatize_reconstruction(
        result: Chapter, instance: ReconstructionPosition
    ) -> Chapter:
        return _lemmatize_reconstruction(lemma, result, instance)

    def lemmatize_manuscript(result: Chapter, instance: ManuscriptPosition) -> Chapter:
        return _lemmatize_manuscript(lemma, result, instance)

    return reduce(
        lemmatize_manuscript,
        MANUSCRIPT_INSTANCES,
        reduce(lemmatize_reconstruction, RECONSTRUCTION_INSTANCES, chapter),
    )


def _find_variant_path(line: int, variant: int) -> TokenPath:
    return ["lines", line, "variants", variant]


def _find_reconstruction_path(instance: ReconstructionPosition) -> TokenPath:
    return [
        *_find_variant_path(instance.line, instance.variant),
        "reconstruction",
        instance.token,
        "uniqueLemma",
    ]


def _find_manuscript_path(instance: ManuscriptPosition) -> TokenPath:
    return [
        *_find_variant_path(instance.line, instance.variant),
        "manuscripts",
        instance.manuscript,
        "line",
        "content",
        instance.token,
        "uniqueLemma",
    ]


def find_changed_token_paths(lemma: Lemma = NEW_LEMMA) -> List[TokenPath]:
    return sorted(
        [
            *(
                _find_reconstruction_path(instance)
                for instance in RECONSTRUCTION_INSTANCES
                if instance.lemma != lemma
            ),
            *(
                _find_manuscript_path(instance)
                for instance in MANUSCRIPT_INSTANCES
                if instance.lemma != lemma
            ),
        ],
        key=str,
    )


def _create_lemmatization(
    tokens: Sequence[Token], word: str
) -> Tuple[LemmatizationToken, ...]:
    return tuple(
        LemmatizationToken(
            token.value,
            NEW_LEMMA
            if token.lemmatizable and token.clean_value == word
            else token.unique_lemma,
        )
        if isinstance(token, AbstractWord)
        else LemmatizationToken(token.value)
        for token in tokens
    )


def create_chapter_lemmatization(
    chapter: Chapter, word: str
) -> List[List[LineVariantLemmatization]]:
    return [
        [
            LineVariantLemmatization(
                _create_lemmatization(variant.reconstruction, word),
                tuple(
                    _create_lemmatization(manuscript_line.get_line_content(), word)
                    for manuscript_line in variant.manuscripts
                ),
            )
            for variant in line.variants
        ]
        for line in chapter.lines
    ]
