from typing import Callable, List

import falcon
import pytest
from falcon import testing

from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.domain.line_snapshot import LineSnapshot
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.transliteration.infrastructure.collections import CHAPTERS_COLLECTION
from ebl.corpus.infrastructure.mongo_text_repository_base import REVISION_FIELD
from ebl.errors import ConflictError, DataError
from ebl.tests.corpus.chapter_edit_support import post_edit
from ebl.tests.corpus.line_annotation_kind import ANNOTATION_QUERY, AnnotationKind
from ebl.tests.corpus.lines_edit_support import (
    OTHER_EDITED_NUMBER,
    count_chapter_changelog_entries,
    find_stored_chapter,
    read_json,
    update_chapter,
)
from ebl.tests.corpus.reference_save_support import ChapterCopies
from ebl.tests.corpus.revision_save_support import LINE_READ_METHOD

OPTIONAL_FIELD = "oldLineNumbers"
FULL_READS = ("find_chapter", "find_chapter_with_revision")
UPDATE_MODULES = (
    "chapter_line_writer.align_line_at",
    "chapter_line_writer.lemmatize_line_at",
    "alignment_updater.align_line_at",
    "lemmatization_updater.lemmatize_line_at",
)
REFUSAL = "refused by the line"


@pytest.fixture
def full_reads(
    text_repository: MongoTextRepository, monkeypatch: pytest.MonkeyPatch
) -> List[str]:
    reads: List[str] = []

    def record(name: str) -> None:
        read = getattr(text_repository, name)

        def record_read(id_: ChapterId) -> object:
            reads.append(name)
            return read(id_)

        monkeypatch.setattr(text_repository, name, record_read)

    for name in FULL_READS:
        record(name)
    return reads


def refuse(*_: object) -> None:
    raise ValueError(REFUSAL)


def test_outline_view_of_a_line_save_does_not_load_the_chapter(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
    full_reads: List[str],
) -> None:
    result = annotation_kind.post_new(client, annotation_chapter, 0)

    assert result.status == falcon.HTTP_OK
    assert full_reads == []


def test_chapter_view_of_a_line_save_loads_the_chapter_after_the_update(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
    full_reads: List[str],
) -> None:
    result = annotation_kind.post_new(client, annotation_chapter, 0, "revision=legacy")

    assert result.status == falcon.HTTP_OK
    assert full_reads == ["find_chapter"]


def test_line_save_does_not_overwrite_a_concurrent_update(
    writer: ChapterEditWriter,
    copies: ChapterCopies,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text_repository = copies.repository
    concurrent_chapter = update_chapter(annotation_chapter, 0, OTHER_EDITED_NUMBER)
    read = text_repository.find_line_with_revision

    def read_before_concurrent_update(id_: ChapterId, index: int) -> LineSnapshot:
        snapshot = read(id_, index)
        text_repository.update(id_, concurrent_chapter)
        return snapshot

    monkeypatch.setattr(
        text_repository, LINE_READ_METHOD, read_before_concurrent_update
    )

    with pytest.raises(ConflictError, match="expected revision legacy"):
        annotation_kind.save_line(writer, annotation_chapter, 0)

    monkeypatch.undo()
    assert (
        text_repository.find_chapter(annotation_chapter.id_).lines
        == concurrent_chapter.lines
    )
    assert (
        text_repository.find_chapter_revision(annotation_chapter.id_) != LEGACY_REVISION
    )
    assert count_chapter_changelog_entries(copies.database) == 0


def test_outline_of_a_line_save_carries_the_revision_of_that_save(
    writer: ChapterEditWriter,
    copies: ChapterCopies,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
) -> None:
    text_repository = copies.repository
    saved = annotation_kind.save_line(writer, annotation_chapter, 0)
    text_repository.update(
        annotation_chapter.id_,
        update_chapter(annotation_chapter, 1, OTHER_EDITED_NUMBER),
    )

    outline = saved.outline

    assert outline.revision == saved.revision
    assert (
        text_repository.find_chapter_revision(annotation_chapter.id_) != saved.revision
    )
    assert outline.lines[1].number == OTHER_EDITED_NUMBER.label


def test_saving_the_stored_annotation_keeps_the_stored_form_of_the_line(
    client: testing.TestClient,
    copies: ChapterCopies,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
) -> None:
    database = copies.database
    database[CHAPTERS_COLLECTION].update_many(
        {}, {"$unset": {f"lines.0.{OPTIONAL_FIELD}": ""}}
    )
    stored_chapter = find_stored_chapter(database, annotation_chapter)
    stored_lines = copies.find_raw_lines(annotation_chapter)
    request = annotation_kind.create_stored_request(annotation_chapter, 0)

    result = post_edit(client, annotation_chapter, request, ANNOTATION_QUERY)

    assert result.status == falcon.HTTP_OK
    assert copies.find_raw_lines(annotation_chapter) == stored_lines
    assert OPTIONAL_FIELD not in stored_chapter["lines"][0]
    assert find_stored_chapter(database, annotation_chapter) == {
        **stored_chapter,
        REVISION_FIELD: read_json(result)["revision"],
    }
    assert count_chapter_changelog_entries(database) == 1


@pytest.mark.parametrize("writer_name", ["writer", "reference_writer"])
def test_invalid_value_in_a_line_update_is_refused_like_on_the_full_path(
    request: pytest.FixtureRequest,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
    assert_nothing_saved: Callable[[], None],
    writer_name: str,
) -> None:
    save_writer: ChapterEditWriter = request.getfixturevalue(writer_name)
    with pytest.MonkeyPatch.context() as patch:
        for module in UPDATE_MODULES:
            patch.setattr(f"ebl.corpus.application.{module}", refuse)
        with pytest.raises(DataError, match=REFUSAL):
            annotation_kind.save_line(save_writer, annotation_chapter, 0)

    assert_nothing_saved()
