from functools import partial
from typing import Callable, Optional

import attr

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.application.lines_updater import LinesUpdater
from ebl.corpus.application.manuscript_reference_injector import (
    inject_references_to_submitted_manuscripts,
)
from ebl.corpus.application.manuscripts_updater import ManuscriptUpdater
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.chapter_revision import require_revision
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.domain.manuscripts_update import ManuscriptsUpdate
from ebl.corpus.domain.parser import parse_chapter
from ebl.users.domain.user import User

ChapterChange = Callable[[Chapter], Chapter]


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

    def _with_stored_revision(self, chapter: Chapter) -> SavedChapter:
        return SavedChapter(
            chapter, self._repository.find_chapter_revision(chapter.id_)
        )

    def _save_at_revision(
        self, id_: ChapterId, change: ChapterChange, revision: str, user: User
    ) -> SavedChapter:
        require_revision(id_, revision, self._repository.find_chapter_revision(id_))
        old_chapter = self.find_chapter(id_)
        updated_chapter = change(old_chapter)
        self._validate_chapter(updated_chapter)
        new_revision = self._repository.update_at_revision(
            id_, updated_chapter, revision
        )
        self._create_changelog(old_chapter, updated_chapter, user)
        return SavedChapter(updated_chapter, new_revision)

    def _change_lines(self, lines: LinesUpdate, chapter: Chapter) -> Chapter:
        return LinesUpdater(lines, self._sign_repository).update(chapter)

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
