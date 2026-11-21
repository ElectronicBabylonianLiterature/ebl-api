from typing import Any, Callable, List, Mapping, Sequence

import attr
import dictdiffer

from ebl.corpus.domain.line import Line
from ebl.corpus.infrastructure.mongo_text_repository_base import REVISION_FIELD
from ebl.tests.corpus.line_annotation_kind import AnnotationKind
from ebl.tests.corpus.line_annotation_kinds import ALIGNMENT, LEMMATIZATION
from ebl.tests.corpus.line_annotation_support import (
    NEW_ALIGNMENTS,
    NEW_MANUSCRIPT_LEMMAS,
    NEW_OMITTED_WORDS,
    NEW_RECONSTRUCTION_LEMMAS,
    find_manuscript_lines,
)
from ebl.tests.corpus.line_move_support import (
    ALIGNED_INDEX,
    LEMMA,
    OMITTED_INDEX,
    OTHER_LEMMA,
    find_words,
)
from ebl.tests.corpus.outline_support import remove_key
from ebl.transliteration.domain.word_tokens import AbstractWord

LineAssertion = Callable[[Line], None]
ALIGNMENT_FIELDS: Sequence[str] = (
    "alignment",
    "variant",
    "omittedWords",
    "hasVariantAlignment",
    "hasOmittedAlignment",
)
LEMMATIZATION_FIELDS: Sequence[str] = ("uniqueLemma",)


def find_reconstruction_words(line: Line) -> Sequence[AbstractWord]:
    return find_words(line.variants[0].reconstruction)


def find_manuscript_words(line: Line) -> Sequence[Sequence[AbstractWord]]:
    return [
        find_words(manuscript_line.get_line_content())
        for manuscript_line in find_manuscript_lines(line)
    ]


def _find_alignment_flags(line: Line) -> Sequence[Sequence[bool]]:
    return [
        [word.has_variant_alignment, word.has_omitted_alignment]
        for word in find_reconstruction_words(line)
    ]


def assert_line_has_the_new_alignment(line: Line) -> None:
    assert [
        [(word.alignment, word.variant) for word in words]
        for words in find_manuscript_words(line)
    ] == [list(NEW_ALIGNMENTS), list(NEW_ALIGNMENTS)]
    assert [
        manuscript_line.omitted_words for manuscript_line in find_manuscript_lines(line)
    ] == [NEW_OMITTED_WORDS, NEW_OMITTED_WORDS]
    assert _find_alignment_flags(line) == [[False, True], [True, False]]


def assert_line_has_the_stored_alignment(line: Line) -> None:
    assert [
        [(word.alignment, word.has_variant) for word in words]
        for words in find_manuscript_words(line)
    ] == [[(ALIGNED_INDEX, True), (None, False)]] * 2
    assert [
        manuscript_line.omitted_words for manuscript_line in find_manuscript_lines(line)
    ] == [(OMITTED_INDEX,), (OMITTED_INDEX,)]
    assert _find_alignment_flags(line) == [[True, False], [False, True]]


def assert_line_has_the_new_lemmas(line: Line) -> None:
    assert [word.unique_lemma for word in find_reconstruction_words(line)] == list(
        NEW_RECONSTRUCTION_LEMMAS
    )
    assert [
        [word.unique_lemma for word in words] for words in find_manuscript_words(line)
    ] == [list(NEW_MANUSCRIPT_LEMMAS), list(NEW_MANUSCRIPT_LEMMAS)]


def assert_line_has_the_stored_lemmas(line: Line) -> None:
    assert [word.unique_lemma for word in find_reconstruction_words(line)] == [
        LEMMA,
        OTHER_LEMMA,
    ]
    assert [
        [word.unique_lemma for word in words] for words in find_manuscript_words(line)
    ] == [[LEMMA, OTHER_LEMMA], [LEMMA, OTHER_LEMMA]]


@attr.s(frozen=True, auto_attribs=True)
class AnnotationCheck:
    kind: AnnotationKind
    assert_saved: LineAssertion
    assert_kept: LineAssertion
    fields: Sequence[str]


ANNOTATION_CHECKS: Sequence[AnnotationCheck] = (
    AnnotationCheck(
        ALIGNMENT,
        assert_line_has_the_new_alignment,
        assert_line_has_the_stored_lemmas,
        ALIGNMENT_FIELDS,
    ),
    AnnotationCheck(
        LEMMATIZATION,
        assert_line_has_the_new_lemmas,
        assert_line_has_the_stored_alignment,
        LEMMATIZATION_FIELDS,
    ),
)


def find_changed_paths(
    old: Mapping[str, Any], new: Mapping[str, Any]
) -> List[List[object]]:
    differences = dictdiffer.diff(
        remove_key(old, REVISION_FIELD), remove_key(new, REVISION_FIELD)
    )
    return [
        path
        for action, node, change in differences
        for path in (
            [node]
            if action == dictdiffer.CHANGE
            else [[*node, key] for key, _ in change]
        )
    ]
