from typing import Optional

import attr

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.application.lines_updater import LinesUpdater
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.chapter_revision import require_revision
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.users.domain.user import User


@attr.s(frozen=True, auto_attribs=True)
class SavedLines:
    chapter: Chapter
    revision: str


class ChapterLinesWriter(Corpus):
    def save_lines(
        self, id_: ChapterId, lines: LinesUpdate, revision: Optional[str], user: User
    ) -> SavedLines:
        return (
            self._save_latest(id_, lines, user)
            if revision is None
            else self._save_at_revision(id_, lines, revision, user)
        )

    def _save_latest(
        self, id_: ChapterId, lines: LinesUpdate, user: User
    ) -> SavedLines:
        chapter = self.update_lines(id_, lines, user)
        return SavedLines(chapter, self._repository.find_chapter_revision(id_))

    def _save_at_revision(
        self, id_: ChapterId, lines: LinesUpdate, revision: str, user: User
    ) -> SavedLines:
        require_revision(id_, revision, self._repository.find_chapter_revision(id_))
        old_chapter = self.find_chapter(id_)
        updated_chapter = LinesUpdater(lines, self._sign_repository).update(old_chapter)
        self._validate_chapter(updated_chapter)
        new_revision = self._repository.update_at_revision(
            id_, updated_chapter, revision
        )
        self._create_changelog(old_chapter, updated_chapter, user)
        return SavedLines(updated_chapter, new_revision)
