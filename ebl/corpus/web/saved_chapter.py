from typing import cast

from ebl.corpus.application.chapter_edit_writer import SavedChapter
from ebl.corpus.application.lines_pagination import LinesView
from ebl.corpus.domain.chapter_outline import ChapterOutline
from ebl.corpus.web.chapter_outline_schemas import ChapterOutlineSchema
from ebl.corpus.web.chapter_schemas import ApiChapterSchema


def dump_saved_chapter(saved: SavedChapter, view: LinesView) -> dict:
    return cast(
        dict,
        ChapterOutlineSchema().dump(
            ChapterOutline.of_chapter(saved.chapter, saved.revision)
        )
        if view is LinesView.OUTLINE
        else ApiChapterSchema().dump(saved.chapter),
    )
