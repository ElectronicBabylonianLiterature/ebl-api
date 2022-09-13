import attr

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.application.signs_updater import SignsUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION


class LinesUpdater(ChapterUpdater):
    def __init__(self, lines: LinesUpdate, sign_repository: SignRepository):
        super().__init__()
        self._lines_update = lines
        self._sign_updater = SignsUpdater(sign_repository)
        self._lines = []

    def _visit_lines(self, chapter: Chapter) -> None:
        for index, line in enumerate(chapter.lines):
            if index in self._lines_update.edited:
                edited_line = self._lines_update.edited[index]
                self._lines.append(
                    attr.evolve(
                        edited_line,
                        variants=tuple(
                            variant.set_alignment_flags()
                            for variant in edited_line.variants
                        ),
                    )
                )
            elif index not in self._lines_update.deleted:
                self._lines.append(
                    attr.evolve(
                        line,
                        variants=tuple(
                            variant.set_alignment_flags() for variant in line.variants
                        ),
                    )
                )

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        return self._sign_updater.update(
            chapter.merge(
                attr.evolve(
                    chapter,
                    lines=(*self._lines, *self._lines_update.new),  # pyre-ignore[60]
                    parser_version=ATF_PARSER_VERSION,
                )
            )
        )
