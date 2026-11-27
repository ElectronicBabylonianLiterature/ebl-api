from functools import reduce
from itertools import product
from typing import Sequence

import attr
import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.infrastructure.mongo_text_repository_base import REVISION_FIELD
from ebl.tests.corpus.line_annotation_assertions import (
    ANNOTATION_CHECKS,
    AnnotationCheck,
    find_changed_paths,
)
from ebl.tests.corpus.line_annotation_kind import AnnotationKind
from ebl.tests.corpus.line_annotation_kinds import ANNOTATION_KINDS
from ebl.tests.corpus.line_annotation_support import (
    ANNOTATION_LINE_COUNT,
    replace_item,
)
from ebl.tests.corpus.line_move_support import LINE_COUNT, STORED_PARSER_VERSION
from ebl.tests.corpus.lines_edit_support import find_stored_chapter
from ebl.tests.corpus.outline_support import remove_key

CHANGED_FIELDS: Sequence[str] = ("lines", REVISION_FIELD)
SIBLING_FIELDS: Sequence[str] = ("name", "_id", REVISION_FIELD)
LINES = pytest.mark.parametrize("index", range(ANNOTATION_LINE_COUNT))
CHECKS = pytest.mark.parametrize(
    "check", ANNOTATION_CHECKS, ids=lambda check: check.kind.name
)


@attr.s(frozen=True, auto_attribs=True)
class SiblingSave:
    kind: AnnotationKind
    index: int
    chapter: Chapter


@pytest.fixture(
    params=product(ANNOTATION_KINDS, range(ANNOTATION_LINE_COUNT)),
    ids=lambda save: f"{save[0].name}-{save[1]}",
)
def sibling_save(
    request: pytest.FixtureRequest,
    corpus: Corpus,
    text_repository: MongoTextRepository,
    annotation_chapter: Chapter,
) -> SiblingSave:
    kind, index = request.param
    sibling = attr.evolve(annotation_chapter, name=f"{annotation_chapter.name} sibling")
    text_repository.create_chapter(sibling)
    kind.save_chapter(corpus, sibling, index)
    return SiblingSave(kind, index, sibling)


@LINES
def test_only_the_annotated_line_changes(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
    index: int,
) -> None:
    stored = text_repository.find_chapter(annotation_chapter.id_)
    annotated_line = annotation_kind.update_line(annotation_chapter, index).lines[index]

    result = annotation_kind.post_new(client, annotation_chapter, index)
    found = text_repository.find_chapter(annotation_chapter.id_)

    assert result.status == falcon.HTTP_OK
    assert found.lines == replace_item(stored.lines, index, annotated_line)
    assert found.lines[index] != stored.lines[index]
    assert found == attr.evolve(stored, lines=found.lines)
    assert found.parser_version == STORED_PARSER_VERSION


@LINES
def test_only_the_annotated_line_changes_in_the_stored_document(
    client: testing.TestClient,
    database: Database,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
    index: int,
) -> None:
    stored_chapter = find_stored_chapter(database, annotation_chapter)

    result = annotation_kind.post_new(client, annotation_chapter, index)
    saved_chapter = find_stored_chapter(database, annotation_chapter)

    assert result.status == falcon.HTTP_OK
    assert saved_chapter["lines"] == list(
        replace_item(stored_chapter["lines"], index, saved_chapter["lines"][index])
    )
    assert saved_chapter["lines"][index] != stored_chapter["lines"][index]
    assert reduce(remove_key, CHANGED_FIELDS, saved_chapter) == reduce(
        remove_key, CHANGED_FIELDS, stored_chapter
    )


@CHECKS
@LINES
def test_only_the_annotation_fields_of_the_line_change_in_the_stored_document(
    client: testing.TestClient,
    database: Database,
    annotation_chapter: Chapter,
    check: AnnotationCheck,
    index: int,
) -> None:
    stored_chapter = find_stored_chapter(database, annotation_chapter)

    check.kind.post_new(client, annotation_chapter, index)
    paths = find_changed_paths(
        stored_chapter, find_stored_chapter(database, annotation_chapter)
    )

    assert paths
    assert [path[:2] for path in paths] == [["lines", index]] * len(paths)
    assert all(set(path).intersection(check.fields) for path in paths)


@CHECKS
@pytest.mark.parametrize("index", range(LINE_COUNT))
def test_annotation_is_stored_and_the_other_annotation_is_kept(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    annotation_chapter: Chapter,
    check: AnnotationCheck,
    index: int,
) -> None:
    result = check.kind.post_new(client, annotation_chapter, index)
    line = text_repository.find_chapter(annotation_chapter.id_).lines[index]

    assert result.status == falcon.HTTP_OK
    check.assert_saved(line)
    check.assert_kept(line)


def test_line_save_stores_what_the_chapter_save_stores(
    client: testing.TestClient,
    database: Database,
    corpus: Corpus,
    annotation_chapter: Chapter,
    sibling_save: SiblingSave,
) -> None:
    sibling = sibling_save.chapter

    result = sibling_save.kind.post_new(client, annotation_chapter, sibling_save.index)

    assert result.status == falcon.HTTP_OK
    assert corpus.find_chapter(annotation_chapter.id_) == attr.evolve(
        corpus.find_chapter(sibling.id_), name=annotation_chapter.name
    )
    assert reduce(
        remove_key, SIBLING_FIELDS, find_stored_chapter(database, annotation_chapter)
    ) == reduce(remove_key, SIBLING_FIELDS, find_stored_chapter(database, sibling))


@LINES
def test_writer_returns_the_chapter_of_the_chapter_updater(
    writer: ChapterEditWriter,
    text_repository: MongoTextRepository,
    annotation_chapter: Chapter,
    annotation_kind: AnnotationKind,
    index: int,
) -> None:
    saved = annotation_kind.save_line(writer, annotation_chapter, index)

    assert saved.chapter == annotation_kind.update_chapter(annotation_chapter, index)
    assert saved.chapter == writer.find_chapter(annotation_chapter.id_)
    assert saved.revision == text_repository.find_chapter_revision(
        annotation_chapter.id_
    )
