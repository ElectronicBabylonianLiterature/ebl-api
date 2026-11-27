from typing import Optional

from ebl.corpus.application.lines_pagination import LinesPageQuery
from ebl.corpus.application.text_repository import TextRepository
from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.domain.chapter_outline import ChapterOutline
from ebl.corpus.domain.chapter_revision import require_revision
from ebl.corpus.domain.lines_page import LinesPage
from ebl.corpus.domain.word_instances import WordInstances


class ChapterEditReader:
    def __init__(self, repository: TextRepository) -> None:
        self._repository = repository

    def find_outline(self, chapter_id: ChapterId) -> ChapterOutline:
        return self._repository.find_chapter_outline(chapter_id)

    def find_lines(
        self, chapter_id: ChapterId, pagination: LinesPageQuery
    ) -> LinesPage:
        page = self._repository.find_lines_page(
            chapter_id, pagination.offset, pagination.limit
        )
        require_revision(chapter_id, pagination.revision, page.revision)
        return page

    def find_word_instances(
        self, chapter_id: ChapterId, word: str, revision: Optional[str]
    ) -> WordInstances:
        chapter, loaded_revision = self._repository.find_chapter_with_revision(
            chapter_id
        )
        require_revision(chapter_id, revision, loaded_revision)
        return WordInstances.of_lines(chapter.lines, word, loaded_revision)
