from typing import Optional, cast

import attr
import pytest

from ebl.bibliography.application.bibliography import Bibliography
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.alignment import Alignment, ManuscriptLineAlignment
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.corpus_test_support import (
    CHAPTER,
    CHAPTER_WITHOUT_DOCUMENTS,
    UpdateDependencies,
    When,
    expect_bibliography,
    expect_find_and_update_chapter,
)
from ebl.tests.corpus.support import ANY_USER
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner
from ebl.transliteration.domain.word_tokens import AbstractWord, Word


@pytest.mark.parametrize(
    "variant",
    [
        None,
        Word.of(
            [
                Reading.of_name("ku"),
            ]
        ),
    ],
)
def test_updating_alignment(
    variant: Optional[Word], corpus: Corpus, update_dependencies: UpdateDependencies
) -> None:
    alignment = 1
    omitted_words = (6,)
    has_variant_alignment = variant is not None
    updated_reconstruction = tuple(
        (
            cast(
                AbstractWord,
                token,
            )
            .set_has_variant_alignment(has_variant_alignment and index == alignment)
            .set_has_omitted_alignment(index in omitted_words)
            if index in (*omitted_words, alignment)
            else token
        )
        for index, token in enumerate(CHAPTER.lines[0].variants[0].reconstruction)
    )
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=(
            attr.evolve(
                CHAPTER.lines[0],
                variants=(
                    attr.evolve(
                        CHAPTER.lines[0].variants[0],
                        reconstruction=updated_reconstruction,
                        manuscripts=(
                            attr.evolve(
                                CHAPTER.lines[0].variants[0].manuscripts[0],
                                line=TextLine.of_iterable(
                                    CHAPTER.lines[0]
                                    .variants[0]
                                    .manuscripts[0]
                                    .line.line_number,
                                    (
                                        Word.of(
                                            [
                                                Reading.of_name("ku"),
                                                Joiner.hyphen(),
                                                BrokenAway.open(),
                                                Reading.of_name("nu"),
                                                Joiner.hyphen(),
                                                Reading.of_name("ši"),
                                                BrokenAway.close(),
                                            ],
                                            alignment=alignment,
                                            variant=variant,
                                        ),
                                    ),
                                ),
                                omitted_words=omitted_words,
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    expect_find_and_update_chapter(
        update_dependencies, CHAPTER_WITHOUT_DOCUMENTS, updated_chapter
    )

    chapter_alignment = Alignment(
        (
            (
                (
                    ManuscriptLineAlignment(
                        (AlignmentToken("ku-[nu-ši]", alignment, variant),),
                        omitted_words,
                    ),
                ),
            ),
        )
    )
    assert (
        corpus.update_alignment(
            CHAPTER.id_, chapter_alignment, update_dependencies.user
        )
        == updated_chapter
    )


@pytest.mark.parametrize(
    "alignment",
    [
        Alignment(
            (
                (
                    (
                        ManuscriptLineAlignment(
                            (
                                AlignmentToken("ku-[nu-ši]", 0),
                                AlignmentToken("ku-[nu-ši]", 0),
                            )
                        ),
                    ),
                ),
            )
        ),
        Alignment(
            (
                (
                    (
                        ManuscriptLineAlignment((AlignmentToken("ku-[nu-ši]", 0),)),
                        ManuscriptLineAlignment((AlignmentToken("ku-[nu-ši]", 0),)),
                    ),
                ),
            )
        ),
        Alignment(
            (
                ((ManuscriptLineAlignment((AlignmentToken("ku-[nu-ši]", 0),)),),),
                ((ManuscriptLineAlignment((AlignmentToken("ku-[nu-ši]", 0),)),),),
            )
        ),
        Alignment((((ManuscriptLineAlignment(()),),),)),
        Alignment((((),),)),
        Alignment(((),)),
        Alignment(()),
        Alignment(
            (((ManuscriptLineAlignment((AlignmentToken("invalid value", 0),)),),),)
        ),
    ],
)
def test_invalid_alignment(
    alignment: Alignment,
    corpus: Corpus,
    text_repository: MongoTextRepository,
    bibliography: Bibliography,
    when: When,
) -> None:
    when(text_repository).find_chapter(CHAPTER.id_).thenReturn(
        CHAPTER_WITHOUT_DOCUMENTS
    )
    expect_bibliography(bibliography, when)
    with pytest.raises(AlignmentError):
        corpus.update_alignment(CHAPTER.id_, alignment, ANY_USER)
