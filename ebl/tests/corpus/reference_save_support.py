from functools import partial, reduce
from typing import Any, Dict, List, Mapping, Sequence

import attr
from bson.raw_bson import RawBSONDocument
from pymongo.database import Database

from ebl.corpus.application.alignment_updater import LineAlignmentUpdater
from ebl.corpus.application.chapter_changes import change_in_place
from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.application.lemmatization import LineLemmatization
from ebl.corpus.application.lemmatization_updater import LineLemmatizationUpdater
from ebl.corpus.application.saved_chapter import SavedChapter
from ebl.corpus.domain.alignment import LineAlignment
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.chapter_change import (
    KEEP_NOTHING,
    ChapterChange,
    KeptContent,
)
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.infrastructure.mongo_text_repository_base import REVISION_FIELD
from ebl.corpus.infrastructure.queries import chapter_id_query
from ebl.tests.corpus.lines_edit_support import find_stored_chapter
from ebl.tests.corpus.outline_support import remove_key
from ebl.transliteration.infrastructure.collections import CHAPTERS_COLLECTION
from ebl.users.domain.user import User

COPY_FIELDS: Sequence[str] = ("_id", "name", REVISION_FIELD, "revision")
SIBLING_SUFFIX = " sibling"


class ReferenceTextRepository(MongoTextRepository):
    def update_at_revision(
        self,
        id_: ChapterId,
        chapter: Chapter,
        revision: str,
        kept: KeptContent = KEEP_NOTHING,
    ) -> str:
        return self._update_at_revision(
            id_, revision, partial(self._create_update, chapter)
        )


class ReferenceChapterEditWriter(ChapterEditWriter):
    def save_line_alignment(
        self, id_: ChapterId, alignment: LineAlignment, revision: str, user: User
    ) -> SavedChapter:
        return self._save_at_revision(
            id_,
            partial(change_in_place, LineAlignmentUpdater(alignment).update),
            revision,
            user,
        )

    def save_line_lemmatization(
        self,
        id_: ChapterId,
        lemmatization: LineLemmatization,
        revision: str,
        user: User,
    ) -> SavedChapter:
        return self._save_at_revision(
            id_,
            partial(change_in_place, LineLemmatizationUpdater(lemmatization).update),
            revision,
            user,
        )


def create_sibling(chapter: Chapter) -> Chapter:
    return attr.evolve(chapter, name=f"{chapter.name}{SIBLING_SUFFIX}")


def remove_copy_fields(document: Mapping[str, Any]) -> Dict[str, Any]:
    return reduce(remove_key, COPY_FIELDS, dict(document))


def find_comparable_chapter(database: Database, chapter: Chapter) -> Dict[str, Any]:
    return remove_copy_fields(find_stored_chapter(database, chapter))


def find_raw_lines(database: Database, chapter: Chapter) -> Sequence[bytes]:
    document = (
        database[CHAPTERS_COLLECTION]
        .with_options(
            codec_options=database.codec_options.with_options(
                document_class=RawBSONDocument
            )
        )
        .find_one(chapter_id_query(chapter.id_))
    )
    assert document is not None
    return [bytes(line.raw) for line in document["lines"]]


@attr.s(frozen=True, auto_attribs=True)
class ChapterCopies:
    database: Database
    repository: MongoTextRepository
    reference: ReferenceTextRepository

    def create_sibling(self, chapter: Chapter) -> Chapter:
        sibling = create_sibling(chapter)
        self.repository.create_chapter(sibling)
        return sibling

    def find_raw_lines(self, chapter: Chapter) -> Sequence[bytes]:
        return find_raw_lines(self.database, chapter)

    def find_kept_lines(self, change: ChapterChange) -> List[bytes]:
        stored_lines = self.find_raw_lines(change.old)
        return [
            stored_lines[run.source + offset]
            for run in change.unchanged_runs
            for offset in range(run.count)
        ]

    def find_kept_positions(self, change: ChapterChange) -> List[int]:
        return [
            run.target + offset
            for run in change.unchanged_runs
            for offset in range(run.count)
        ]

    def update(self, change: ChapterChange, revision: str = LEGACY_REVISION) -> str:
        return self.repository.update_at_revision(
            change.old.id_, change.new, revision, change.kept
        )

    def update_fully(
        self, sibling: Chapter, chapter: Chapter, revision: str = LEGACY_REVISION
    ) -> str:
        return self.reference.update_at_revision(sibling.id_, chapter, revision)

    def assert_equal(self, chapter: Chapter, sibling: Chapter) -> None:
        assert find_comparable_chapter(
            self.database, chapter
        ) == find_comparable_chapter(self.database, sibling)

    def assert_updates_like_the_full_update(self, change: ChapterChange) -> None:
        sibling = self.create_sibling(change.old)
        kept_lines = self.find_kept_lines(change)
        self.update(change)
        self.update_fully(sibling, change.new)
        stored_lines = self.find_raw_lines(change.old)
        self.assert_equal(change.old, sibling)
        assert [
            stored_lines[position] for position in self.find_kept_positions(change)
        ] == kept_lines
        found = self.repository.find_chapter(change.old.id_)
        assert found.lines == change.new.lines
        assert found == attr.evolve(
            self.repository.find_chapter(sibling.id_), name=found.name
        )
