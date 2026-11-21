import pytest

from ebl.corpus.domain.chapter import Chapter
from ebl.tests.corpus.line_annotation_assertions import (
    ANNOTATION_CHECKS,
    AnnotationCheck,
    find_manuscript_words,
)
from ebl.tests.corpus.line_annotation_kind import AnnotationKind
from ebl.tests.corpus.line_annotation_kinds import ALIGNMENT, LEMMATIZATION
from ebl.tests.corpus.line_annotation_support import (
    ANNOTATION_LINE_COUNT,
    NEW_MANUSCRIPT_LEMMAS,
    NEW_OMITTED_WORDS,
    NEW_RECONSTRUCTION_LEMMAS,
    NEW_VARIANT,
    SPECIAL_INDEX,
    create_annotation_chapter,
    find_manuscript_lines,
)
from ebl.tests.corpus.line_move_support import (
    LINE_COUNT,
    assert_lines_are_annotated,
    find_words,
)

LINES = pytest.mark.parametrize("index", range(ANNOTATION_LINE_COUNT))


@pytest.fixture
def chapter() -> Chapter:
    return create_annotation_chapter()


def test_lines_of_the_chapter_are_annotated(chapter: Chapter) -> None:
    assert_lines_are_annotated(chapter.lines[:LINE_COUNT])
    assert len(chapter.lines) == ANNOTATION_LINE_COUNT


@LINES
def test_line_update_equals_the_chapter_update_with_only_that_line_replaced(
    chapter: Chapter, annotation_kind: AnnotationKind, index: int
) -> None:
    updated_chapter = annotation_kind.update_line(chapter, index)

    assert updated_chapter == annotation_kind.update_chapter(chapter, index)
    assert updated_chapter.lines[index] != chapter.lines[index]


@LINES
def test_line_update_keeps_every_other_line_and_the_rest_of_the_chapter(
    chapter: Chapter, annotation_kind: AnnotationKind, index: int
) -> None:
    updated_chapter = annotation_kind.update_line(chapter, index)

    assert [
        updated_line is chapter.lines[line_index]
        for line_index, updated_line in enumerate(updated_chapter.lines)
    ] == [line_index != index for line_index in range(ANNOTATION_LINE_COUNT)]
    assert updated_chapter.signs == chapter.signs
    assert updated_chapter.parser_version == chapter.parser_version
    assert updated_chapter.manuscripts == chapter.manuscripts


@pytest.mark.parametrize("check", ANNOTATION_CHECKS, ids=lambda check: check.kind.name)
@pytest.mark.parametrize("index", range(LINE_COUNT))
def test_updated_line_has_the_new_annotation_and_keeps_the_other_one(
    chapter: Chapter, check: AnnotationCheck, index: int
) -> None:
    line = check.kind.update_line(chapter, index).lines[index]

    check.assert_saved(line)
    check.assert_kept(line)


def test_special_line_is_aligned_per_variant(chapter: Chapter) -> None:
    line = ALIGNMENT.update_line(chapter, SPECIAL_INDEX).lines[SPECIAL_INDEX]
    text_line, empty_line = find_manuscript_lines(line)
    aligned_word, unclear_word = find_words(text_line.get_line_content())
    flags = [
        [
            (word.has_variant_alignment, word.has_omitted_alignment)
            for word in find_words(variant.reconstruction)
        ]
        for variant in line.variants
    ]

    assert (aligned_word.alignment, aligned_word.variant) == (3, NEW_VARIANT)
    assert (unclear_word.alignment, unclear_word.variant) == (None, None)
    assert text_line.omitted_words == empty_line.omitted_words == NEW_OMITTED_WORDS
    assert empty_line.is_empty
    assert flags == [[(False, True), (True, False)], [(False, False)]]


def test_special_line_is_lemmatized_per_variant(chapter: Chapter) -> None:
    line = LEMMATIZATION.update_line(chapter, SPECIAL_INDEX).lines[SPECIAL_INDEX]
    (manuscript_words, _) = find_manuscript_words(line)

    assert [
        [word.unique_lemma for word in find_words(variant.reconstruction)]
        for variant in line.variants
    ] == [[NEW_RECONSTRUCTION_LEMMAS[0], ()], [NEW_RECONSTRUCTION_LEMMAS[0]]]
    assert [word.unique_lemma for word in manuscript_words] == [
        NEW_MANUSCRIPT_LEMMAS[0],
        (),
    ]
