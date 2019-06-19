from ebl.corpus.api_serializer import ApiSerializer
from ebl.corpus.text import TextId, Text
from ebl.errors import NotFoundError


def create_text_id(category: str, index: str) -> TextId:
    try:
        return TextId(int(category), int(index))
    except ValueError:
        raise NotFoundError(f'Text {category}.{index} not found.')


def serialize_public_text(text: Text):
    return ApiSerializer.serialize_public(text)
