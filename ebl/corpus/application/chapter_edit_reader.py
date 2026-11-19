from ebl.corpus.application.lines_pagination import LinesPageQuery
from ebl.corpus.application.text_repository import TextRepository
from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.domain.chapter_outline import ChapterOutline
from ebl.corpus.domain.lines_page import LinesPage


class ChapterEditReader:
    def __init__(self, repository: TextRepository) -> None:
        self._repository = repository

    def find_outline(self, chapter_id: ChapterId) -> ChapterOutline:
        return self._repository.find_chapter_outline(chapter_id)

    def find_lines(
        self, chapter_id: ChapterId, pagination: LinesPageQuery
    ) -> LinesPage:
        return self._repository.find_lines_page(
            chapter_id, pagination.offset, pagination.limit
        )
