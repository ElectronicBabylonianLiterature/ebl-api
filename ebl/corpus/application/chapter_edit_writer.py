from functools import partial
from typing import Callable, Optional

import attr

from ebl.changelog import create_entry, is_storable
from ebl.corpus.application.alignment_updater import LineAlignmentUpdater
from ebl.corpus.application.chapter_changelog import (
    ChapterDiff,
    ChapterDiffer,
    create_chapter_diff,
    create_line_move_diff,
)
from ebl.corpus.application.corpus import COLLECTION, Corpus
from ebl.corpus.application.lemmatization import LineLemmatization
from ebl.corpus.application.lemmatization_updater import LineLemmatizationUpdater
from ebl.corpus.application.line_move_updater import LineMoveUpdater
from ebl.corpus.application.lines_updater import LinesUpdater
from ebl.corpus.application.manuscript_reference_injector import (
    inject_references_to_submitted_manuscripts,
)
from ebl.corpus.application.manuscripts_updater import ManuscriptUpdater
from ebl.corpus.domain.alignment import LineAlignment
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.chapter_revision import require_revision
from ebl.corpus.domain.line_move import LineMove
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.domain.manuscripts_update import ManuscriptsUpdate
from ebl.corpus.domain.parser import parse_chapter
from ebl.errors import DataError
from ebl.users.domain.user import User

ChapterChange = Callable[[Chapter], Chapter]
CHANGE_TOO_LARGE = (
    "The change is too large to be recorded in the changelog. Nothing was saved."
)


@attr.s(frozen=True, auto_attribs=True)
class SavedChapter:
    chapter: Chapter
    revision: str


class ChapterEditWriter(Corpus):
    def save_lines(
        self, id_: ChapterId, lines: LinesUpdate, revision: Optional[str], user: User
    ) -> SavedChapter:
        return (
            self._with_stored_revision(self.update_lines(id_, lines, user))
            if revision is None
            else self._save_at_revision(
                id_, partial(self._change_lines, lines), revision, user
            )
        )

    def save_imported_lines(
        self, id_: ChapterId, atf: str, revision: Optional[str], user: User
    ) -> SavedChapter:
        return (
            self._with_stored_revision(self.import_lines(id_, atf, user))
            if revision is None
            else self._save_at_revision(
                id_, partial(self._import_lines, atf), revision, user
            )
        )

    def save_manuscripts(
        self,
        id_: ChapterId,
        update: ManuscriptsUpdate,
        revision: Optional[str],
        user: User,
    ) -> SavedChapter:
        return (
            self._with_stored_revision(
                self.update_manuscripts(
                    id_, update.manuscripts, update.uncertain_fragments, user
                )
            )
            if revision is None
            else self._save_at_revision(
                id_, partial(self._change_manuscripts, update), revision, user
            )
        )

    def move_line(
        self, id_: ChapterId, move: LineMove, revision: str, user: User
    ) -> SavedChapter:
        return self._save_at_revision(
            id_,
            partial(self._move_line, move),
            revision,
            user,
            partial(create_line_move_diff, move),
        )

    def save_line_alignment(
        self, id_: ChapterId, alignment: LineAlignment, revision: str, user: User
    ) -> SavedChapter:
        return self._save_at_revision(
            id_, LineAlignmentUpdater(alignment).update, revision, user
        )

    def save_line_lemmatization(
        self,
        id_: ChapterId,
        lemmatization: LineLemmatization,
        revision: str,
        user: User,
    ) -> SavedChapter:
        return self._save_at_revision(
            id_, LineLemmatizationUpdater(lemmatization).update, revision, user
        )

    def _with_stored_revision(self, chapter: Chapter) -> SavedChapter:
        return SavedChapter(
            chapter, self._repository.find_chapter_revision(chapter.id_)
        )

    def _save_at_revision(
        self,
        id_: ChapterId,
        change: ChapterChange,
        revision: str,
        user: User,
        create_diff: ChapterDiffer = create_chapter_diff,
    ) -> SavedChapter:
        old_chapter = self._find_chapter_at_revision(id_, revision)
        updated_chapter = change(old_chapter)
        self._validate_chapter(updated_chapter)
        entry = self._prepare_changelog_entry(
            old_chapter.id_, create_diff(old_chapter, updated_chapter), user
        )
        new_revision = self._repository.update_at_revision(
            id_, updated_chapter, revision
        )
        self._changelog.insert(entry)
        return SavedChapter(updated_chapter, new_revision)

    def _find_chapter_at_revision(self, id_: ChapterId, revision: str) -> Chapter:
        chapter, loaded_revision = self._repository.find_chapter_with_revision(id_)
        require_revision(id_, revision, loaded_revision)
        return self._inject_references(chapter)

    def _prepare_changelog_entry(
        self, id_: ChapterId, diff: ChapterDiff, user: User
    ) -> dict:
        entry = create_entry(user.profile, COLLECTION, id_.to_tuple(), diff)
        if not is_storable(entry):
            raise DataError(CHANGE_TOO_LARGE)
        return entry

    def _change_lines(self, lines: LinesUpdate, chapter: Chapter) -> Chapter:
        return LinesUpdater(lines, self._sign_repository).update(chapter)

    def _move_line(self, move: LineMove, chapter: Chapter) -> Chapter:
        return LineMoveUpdater(move, self._sign_repository).update(chapter)

    def _import_lines(self, atf: str, chapter: Chapter) -> Chapter:
        lines = parse_chapter(atf, chapter.manuscripts, self._provenance_service)
        return self._change_lines(LinesUpdate(lines, set(), {}), chapter)

    def _change_manuscripts(
        self, update: ManuscriptsUpdate, chapter: Chapter
    ) -> Chapter:
        return ManuscriptUpdater(
            inject_references_to_submitted_manuscripts(
                self._bibliography, update.manuscripts
            ),
            update.uncertain_fragments,
            self._sign_repository,
        ).update(chapter)
