from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.domain.text import TextId
from ebl.errors import NotFoundError
from ebl.corpus.domain.stage import Stage


def create_text_id(category: str, index: str) -> TextId:
    try:
        return TextId(int(category), int(index))
    except ValueError:
        raise NotFoundError(f"Text {category}.{index} not found.")


def create_chapter_id(category: str, index: str, stage: str, name: str) -> ChapterId:
    try:
        return ChapterId(create_text_id(category, index), Stage(stage), name)
    except ValueError:
        raise NotFoundError(f"Chapter {category}.{index} {stage} {name} not found.")
