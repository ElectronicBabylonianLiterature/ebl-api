from functools import partial
from typing import Callable, Mapping

import attr

from ebl.changelog import create_entry, is_storable
from ebl.corpus.application.alignment_updater import align_line_at
from ebl.corpus.application.chapter_changelog import ChapterDiff, create_line_diff
from ebl.corpus.application.chapter_edit_reader import ChapterEditReader
from ebl.corpus.application.chapter_updater import try_update
from ebl.corpus.application.corpus import COLLECTION, Corpus
from ebl.corpus.application.lemmatization import LineLemmatization
from ebl.corpus.application.lemmatization_updater import lemmatize_line_at
from ebl.corpus.application.line_updater import create_invalid_line_error
from ebl.corpus.application.saved_chapter import SavedChapter
from ebl.corpus.application.text_validator import validate_line
from ebl.corpus.domain.alignment import LineAlignment
from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.domain.chapter_outline import ChapterOutline
from ebl.corpus.domain.chapter_revision import require_revision
from ebl.corpus.domain.line import Line
from ebl.errors import DataError
from ebl.users.domain.user import User

LineUpdate = Callable[[Line], Line]
CHANGE_TOO_LARGE = (
    "The change is too large to be recorded in the changelog. Nothing was saved."
)


def _find_changed_lines(index: int, old: Line, new: Line) -> Mapping[int, Line]:
    return {} if new == old else {index: new}


class ChapterLineWriter(Corpus):
    def save_line_alignment(
        self, id_: ChapterId, alignment: LineAlignment, revision: str, user: User
    ) -> SavedChapter:
        return self._save_line_at_revision(
            id_, alignment.index, partial(align_line_at, alignment), revision, user
        )

    def save_line_lemmatization(
        self,
        id_: ChapterId,
        lemmatization: LineLemmatization,
        revision: str,
        user: User,
    ) -> SavedChapter:
        return self._save_line_at_revision(
            id_,
            lemmatization.index,
            partial(lemmatize_line_at, lemmatization),
            revision,
            user,
        )

    def _save_line_at_revision(
        self, id_: ChapterId, index: int, update: LineUpdate, revision: str, user: User
    ) -> SavedChapter:
        snapshot = self._repository.find_line_with_revision(id_, index)
        require_revision(id_, revision, snapshot.revision)
        old_line = snapshot.line
        if old_line is None:
            raise create_invalid_line_error(index, snapshot.line_count)
        new_line = try_update(lambda: update(old_line))
        validate_line(new_line, snapshot.manuscripts)
        entry = self._prepare_changelog_entry(
            id_, create_line_diff(index, old_line, new_line), user
        )
        new_revision = self._repository.update_lines_at_revision(
            id_, _find_changed_lines(index, old_line, new_line), revision
        )
        self._changelog.insert(entry)
        return SavedChapter(
            new_revision,
            partial(self.find_chapter, id_),
            partial(self._find_outline_at, id_, new_revision),
        )

    def _find_outline_at(self, id_: ChapterId, revision: str) -> ChapterOutline:
        return attr.evolve(
            ChapterEditReader(self._repository).find_outline(id_), revision=revision
        )

    def _prepare_changelog_entry(
        self, id_: ChapterId, diff: ChapterDiff, user: User
    ) -> dict:
        entry = create_entry(user.profile, COLLECTION, id_.to_tuple(), diff)
        if not is_storable(entry):
            raise DataError(CHANGE_TOO_LARGE)
        return entry
