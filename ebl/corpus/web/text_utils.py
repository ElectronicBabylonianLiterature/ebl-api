from ebl.corpus.domain.text import Text, TextId
from ebl.corpus.web.api_serializer import ApiSerializer
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


def serialize_public_text(text: Text):
    return ApiSerializer.serialize_public(text)
