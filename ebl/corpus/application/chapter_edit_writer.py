from functools import partial
from typing import Optional

from ebl.corpus.application.chapter_changelog import create_change_diff
from ebl.corpus.application.chapter_changes import (
    ChapterChanger,
    change_in_place,
    change_lines,
    move_line,
)
from ebl.corpus.application.chapter_line_writer import (
    CHANGE_TOO_LARGE,
    ChapterLineWriter,
)
from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.application.lines_updater import LinesUpdater
from ebl.corpus.application.manuscript_reference_injector import (
    inject_references_to_submitted_manuscripts,
)
from ebl.corpus.application.manuscripts_updater import ManuscriptUpdater
from ebl.corpus.application.saved_chapter import SavedChapter
from ebl.corpus.application.word_instances_updater import WordInstancesLemmatizer
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.chapter_change import ChapterChange
from ebl.corpus.domain.chapter_revision import require_revision
from ebl.corpus.domain.line_move import LineMove
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.domain.manuscripts_update import ManuscriptsUpdate
from ebl.corpus.domain.parser import parse_chapter
from ebl.corpus.domain.word_instances import WordLemma
from ebl.users.domain.user import User

__all__ = ["CHANGE_TOO_LARGE", "ChapterEditWriter", "SavedChapter"]


class ChapterEditWriter(ChapterLineWriter):
    def save_lines(
        self, id_: ChapterId, lines: LinesUpdate, revision: Optional[str], user: User
    ) -> SavedChapter:
        return (
            self._save_without_revision(
                id_, LinesUpdater(lines, self._sign_repository), user
            )
            if revision is None
            else self._save_at_revision(
                id_, partial(change_lines, lines, self._sign_repository), revision, user
            )
        )

    def save_imported_lines(
        self, id_: ChapterId, atf: str, revision: Optional[str], user: User
    ) -> SavedChapter:
        return (
            self._save_without_revision(
                id_,
                LinesUpdater(self._parse_lines(id_, atf), self._sign_repository),
                user,
            )
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
            self._save_without_revision(
                id_,
                self._create_manuscript_updater(update),
                user,
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
            id_, partial(move_line, move, self._sign_repository), revision, user
        )

    def save_word_lemma(
        self, id_: ChapterId, word_lemma: WordLemma, revision: str, user: User
    ) -> SavedChapter:
        return self._save_at_revision(
            id_,
            partial(change_in_place, WordInstancesLemmatizer(word_lemma).update),
            revision,
            user,
        )

    def _save_without_revision(
        self, id_: ChapterId, updater: ChapterUpdater, user: User
    ) -> SavedChapter:
        old_chapter = self.find_chapter(id_)
        new_chapter = updater.update(old_chapter)
        return SavedChapter.of_chapter(
            new_chapter, self.update_chapter(id_, old_chapter, new_chapter, user)
        )

    def _parse_lines(self, id_: ChapterId, atf: str) -> LinesUpdate:
        manuscripts = self.find_chapter(id_).manuscripts
        return LinesUpdate(
            parse_chapter(atf, manuscripts, self._provenance_service), set(), {}
        )

    def _save_at_revision(
        self, id_: ChapterId, change: ChapterChanger, revision: str, user: User
    ) -> SavedChapter:
        chapter_change = change(self._find_chapter_at_revision(id_, revision))
        if chapter_change.new == chapter_change.old:
            return SavedChapter.of_chapter(chapter_change.new, revision)
        self._validate_chapter(chapter_change.new)
        entry = self._prepare_changelog_entry(
            chapter_change.old.id_, create_change_diff(chapter_change), user
        )
        new_revision = self._repository.update_at_revision(
            id_, chapter_change.new, revision, chapter_change.kept
        )
        self._changelog.insert(entry)
        return SavedChapter.of_chapter(chapter_change.new, new_revision)

    def _find_chapter_at_revision(self, id_: ChapterId, revision: str) -> Chapter:
        chapter, loaded_revision = self._repository.find_chapter_with_revision(id_)
        require_revision(id_, revision, loaded_revision)
        return self._inject_references(chapter)

    def _import_lines(self, atf: str, chapter: Chapter) -> ChapterChange:
        lines = parse_chapter(atf, chapter.manuscripts, self._provenance_service)
        return change_lines(
            LinesUpdate(lines, set(), {}), self._sign_repository, chapter
        )

    def _change_manuscripts(
        self, update: ManuscriptsUpdate, chapter: Chapter
    ) -> ChapterChange:
        return change_in_place(
            self._create_manuscript_updater(update).update,
            chapter,
        )

    def _create_manuscript_updater(
        self, update: ManuscriptsUpdate
    ) -> ManuscriptUpdater:
        return ManuscriptUpdater(
            inject_references_to_submitted_manuscripts(
                self._bibliography, update.manuscripts
            ),
            update.uncertain_fragments,
            self._sign_repository,
        )
