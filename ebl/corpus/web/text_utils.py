from ebl.corpus.domain.text import TextId
from ebl.errors import NotFoundError


def create_text_id(category: str, index: str) -> TextId:
    try:
        return TextId(int(category), int(index))
    except ValueError:
        raise NotFoundError(f"Text {category}.{index} not found.")


def create_chapter_index(chapter_index: str) -> int:
    try:
        return int(chapter_index)
    except ValueError:
        raise NotFoundError(f"Chapter {chapter_index} not found.")
