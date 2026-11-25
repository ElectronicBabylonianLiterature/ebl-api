from typing import cast

import attr

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.tests.corpus.corpus_test_support import (
    CHAPTER,
    CHAPTER_WITHOUT_DOCUMENTS,
    UpdateDependencies,
    expect_find_and_update_chapter,
)
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner
from ebl.transliteration.domain.word_tokens import AbstractWord, Word


def test_updating_lines_edit(
    corpus: Corpus, update_dependencies: UpdateDependencies
) -> None:
    omitted_words = tuple(
        index
        for manuscript in CHAPTER.lines[0].variants[0].manuscripts
        for index in manuscript.omitted_words
    )
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=(
            attr.evolve(
                CHAPTER.lines[0].set_variant_alignment_flags(),
                number=LineNumber(1, True),
                variants=(
                    attr.evolve(
                        CHAPTER.lines[0].variants[0],
                        manuscripts=(
                            attr.evolve(
                                CHAPTER.lines[0].variants[0].manuscripts[0],
                                line=TextLine.of_iterable(
                                    LineNumber(1, True),
                                    (
                                        Word.of(
                                            [
                                                Reading.of_name("nu"),
                                                Joiner.hyphen(),
                                                BrokenAway.open(),
                                                Reading.of_name("ku"),
                                                Joiner.hyphen(),
                                                Reading.of_name("ši"),
                                                BrokenAway.close(),
                                            ]
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        reconstruction=tuple(
                            (
                                cast(
                                    AbstractWord,
                                    token,
                                ).set_has_omitted_alignment(True)
                                if index in omitted_words
                                else token
                            )
                            for index, token in enumerate(
                                CHAPTER.lines[0].variants[0].reconstruction
                            )
                        ),
                    ),
                ),
            ).set_variant_alignment_flags(),
        ),
        signs=("ABZ075 KU ABZ207a\\u002F207b\\u0020X\nKU\nABZ075",),
        parser_version=ATF_PARSER_VERSION,
    )
    expect_find_and_update_chapter(
        update_dependencies, CHAPTER_WITHOUT_DOCUMENTS, updated_chapter
    )

    assert (
        corpus.update_lines(
            CHAPTER.id_,
            LinesUpdate([], set(), {0: updated_chapter.lines[0]}),
            update_dependencies.user,
        )
        == updated_chapter
    )


def test_updating_lines_delete(
    corpus: Corpus, update_dependencies: UpdateDependencies
) -> None:
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=CHAPTER.lines[1:],
        signs=("KU\nABZ075",),
        parser_version=ATF_PARSER_VERSION,
    )
    expect_find_and_update_chapter(
        update_dependencies, CHAPTER_WITHOUT_DOCUMENTS, updated_chapter
    )

    assert (
        corpus.update_lines(
            CHAPTER.id_, LinesUpdate([], {0}, {}), update_dependencies.user
        )
        == updated_chapter
    )


def test_updating_lines_add(
    corpus: Corpus, update_dependencies: UpdateDependencies
) -> None:
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=(
            CHAPTER.lines[0].set_variant_alignment_flags(),
            attr.evolve(
                CHAPTER.lines[0],
                number=LineNumber(2, True),
                variants=(
                    attr.evolve(
                        CHAPTER.lines[0].variants[0],
                        manuscripts=(
                            attr.evolve(
                                CHAPTER.lines[0].variants[0].manuscripts[0],
                                line=TextLine.of_iterable(
                                    LineNumber(2, True),
                                    (Word.of([Reading.of_name("nu")]),),
                                ),
                            ),
                        ),
                    ),
                ),
            ).set_variant_alignment_flags(),
        ),
        signs=("KU ABZ075 ABZ207a\\u002F207b\\u0020X\nABZ075\nKU\nABZ075",),
        parser_version=ATF_PARSER_VERSION,
    )
    expect_find_and_update_chapter(
        update_dependencies, CHAPTER_WITHOUT_DOCUMENTS, updated_chapter
    )

    assert (
        corpus.update_lines(
            CHAPTER.id_,
            LinesUpdate([updated_chapter.lines[1]], set(), {}),
            update_dependencies.user,
        )
        == updated_chapter
    )
